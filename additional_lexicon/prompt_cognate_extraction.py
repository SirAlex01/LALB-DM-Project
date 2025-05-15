import csv
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import os
import google.generativeai as genai
import time
from tqdm import tqdm
import pickle
import random
import json
from collections import OrderedDict

# recall proper names types: anthroponym, ethnonym, phytonym, toponym, patronymic, theonym


# Load environment variables from .env file
load_dotenv()

# Retrieve the API key

api_keys = [os.getenv("GOOGLE_API_KEY_1"), os.getenv("GOOGLE_API_KEY_2"), os.getenv("GOOGLE_API_KEY_3"), os.getenv("GOOGLE_API_KEY_4"), os.getenv("GOOGLE_API_KEY_5")
            , os.getenv("GOOGLE_API_KEY_6"), os.getenv("GOOGLE_API_KEY_7"), os.getenv("GOOGLE_API_KEY_8"), os.getenv("GOOGLE_API_KEY_9")]

def make_prompt(info_dict, api_key):
    # Create the root XML element
    prompt = ET.Element("root")
    
    # Introduction to Linear B
    intro = ET.SubElement(prompt, "introduction")
    intro.text = """
    Linear B is a syllabic script used for writing Mycenaean Greek (1450-1200 BCE). It consists of syllabic signs 
    and ideograms, and has been deciphered as an early form of Greek. Your task is to process Linear B words and 
    their Greek cognates according to specific linguistic rules, standardizing the output format and handling 
    various linguistic phenomena correctly.
    """
    
    # Add the Linear B data
    data_element = ET.SubElement(prompt, "linear_b_data")
    for key, value in info_dict.items():
        field = ET.SubElement(data_element, "field", name=key)
        field.text = value
    
    # Historical context and linguistic principles
    principles = ET.SubElement(prompt, "rules")
    principles.text = """
    PROCESSING RULES FOR LINEAR B TO GREEK COGNATES:
    
    0. CRITICAL: DO NOT MAKE ANY MODIFICATION TO GREEK COGNATES OR LINEAR B SEQUENCES IF THE MODIFICATION IS NOT MENTIONED IN THE FOLLOWING RULES! DO NOT CHANGE THE INPUT IN ANY POSSIBBLE WAY AND ONLY APPLY THE GIVEN MODIFICATION RULES! NO FANTASY JUST BLINDLY OBEY!

    1. SPLITTING MULTIPLE WORDS: When Linear B field contains multiple words separated by "/", create separate JSON objects for each word, matching with the corresponding Greek cognate in the same position.
    
    2. HANDLING PARENTHESES: For Linear B words with parenthetical elements like "po-ni-ke-(j)a", create two separate entries (one with and one without the parenthetical element, like "po-ni-ke-ja" and "po-ni-ke-a").
    
    2.2 HANDLING PARENTHESES FOR GREEK COGNATE: if a word is presented with optional greek characters with parenthetical elements like "αιξμά(ν)ς", include both variants with and without the letter in parenthesis. 

    2.3 HANDLING PARENTHESES FOR GREEK COGNATE: if a word is presented within parentheses, include it regardless, like "Αιθαλεύσι(Αιθαλεύς)". 

    3. MULTIPLE TRANSLATIONS: If a Linear B word has multiple possible Greek cognates, include all of them as an array within the same JSON object.
    
    4. REMOVING DIACRITICS: Remove all accents, breathing marks, and other diacritics from Greek cognates.
    
    5. HANDLING "ha" SIGN: When "ha" appears in Linear B, ensure the corresponding Greek cognate includes "h".
    
    6. DIGAMMA CONVERSION: Convert every instance of digamma "F" to lowercase "f" in Greek cognates.
    
    7. CRITICAL: ALLOWED CHARACTERS: Use ONLY these characters in Greek cognates: fhαβγδεζηθικλμνξοπρςστυφχψω. DO NOT USE ANY OTHER CHARACTER FOR ANY REASON!
    
    8. DISALLOWED CHARACTERS: Drop cognates containing disallowed characters, but preserve valid cognates found within parentheses or other markers.
    
    9. IN SOME VERY RARE AND PARTICULAR CASES some cognates may be considered as DUBIOUS, IF AND ONLY IF THEY CONTAIN A LIKELY WRONG TRANSLITERATION AND A CORRECT MATCH IS ALREADY PRESENT. Put them in the "dubious" field, another optional array field in the JSON object.

    10 if white spaces are present between syllables separated by - are present in the linear b sequence, remove them.
    
    11. DO NOT USE PARENTHESES IN THE LINEAR B SEQUENCES OR IN THE GREEK COGNATE.
    
    The final output must be a JSON array containing a separate JSON object for each processed Linear B word, with fields for the Linear B word, its Greek cognate(s) as an array, and a detailed explanation of the processing applied, and optionally a dubious array field.
    """
    
    # Output format description with detailed examples for each rule
    examples = ET.SubElement(prompt, "examples")
    examples.text = """
    EXAMPLES FOR EACH RULE:
    
    RULE 1 - Multiple words separated by "/":
    INPUT: 
      linear_b: "ke-ra/ke-ra-ha", 
      greek_cognate: "κέρας/κέραhα", 
      transliteration: "keras/keraha", 
      meaning: "horn"
    
    OUTPUT:
    [
      {
        "linear_b": "ke-ra",
        "greek_cognates": ["κερας"],
        "explanation": "First word from the pair. Removed accent from 'έ'. The Linear B 'ke-ra' corresponds to Greek 'κερας' (horn)."
      },
      {
        "linear_b": "ke-ra-ha",
        "greek_cognates": ["κεραhα"],
        "explanation": "Second word from the pair. Removed accent from 'έ'. The ha sign in Linear B indicates aspiration, represented by 'h' in the Greek cognate."
      }
    ]
    
    RULE 2 - Words with parentheses:
    INPUT:
      linear_b: "po-ni-ke-(j)a", 
      greek_cognate: "φοινίκεια", 
      transliteration: "phoinikeia", 
      meaning: "purple"
    
    OUTPUT:
    [
      {
        "linear_b": "po-ni-ke-a",
        "greek_cognates": ["φοινικεια"],
        "explanation": "First variant without the optional 'j'. Removed accent from 'ί'. The Linear B 'po-ni-ke-a' corresponds to Greek 'φοινικεια'."
      },
      {
        "linear_b": "po-ni-ke-ja",
        "greek_cognates": ["φοινικεια"],
        "explanation": "Second variant with the optional 'j'. Removed accent from 'ί'. The Linear B 'po-ni-ke-ja' corresponds to Greek 'φοινικεια'."
      }
    ]
    
    RULE 3 - Multiple possible translations:
    INPUT:
      linear_b: "a-to-ro-qo", 
      greek_cognate: "ἄνθρωπος/ἀνθρώπῳ", 
      transliteration: "anthropos/anthropoi", 
      meaning: "man/to the man"
    
    OUTPUT:
    [
      {
        "linear_b": "a-to-ro-qo",
        "greek_cognates": ["ανθρωπος", "ανθρωπω"],
        "explanation": "Multiple possible cognates. Removed all accents and breathing marks. The Linear B 'a-to-ro-qo' can correspond to either 'ανθρωπος' (man) or 'ανθρωπω' (to the man)."
      }
    ]
    
    RULE 4 - Handling accents and diacritics:
    INPUT:
      linear_b: "su-za", 
      greek_cognate: "σύζα (σύkΥα> σύκα)", 
      transliteration: "syza (sykYa> syka)", 
      meaning: "fig fruits"
    
    OUTPUT:
    [
      {
        "linear_b": "su-za",
        "greek_cognates": ["συζα", "συκα"],
        "explanation": "Removed accents from 'ύ'. Ignored 'Y' as it's not in allowed characters. Both cognates 'συζα' and 'συκα' are included."
      }
    ]
    
    RULE 5 - Handling "ha" or "ha":
    INPUT:
      linear_b: "te-tu-ku-wo-a/te-tu-ku-wo-ha", 
      greek_cognate: "τετυχύFοα/τετυχύFοhα", 
      transliteration: "tetyhyvoa/tetyhyvoha", 
      meaning: "well prepared, ready"
    
    OUTPUT:
    [
      {
        "linear_b": "te-tu-ku-wo-a",
        "greek_cognates": ["τετυχυfοα"],
        "explanation": "First form without ha. Removed accent from 'ύ'. Converted digamma 'F' to lowercase 'f'."
      },
      {
        "linear_b": "te-tu-ku-wo-ha",
        "greek_cognates": ["τετυχυfοhα"],
        "explanation": "Second form with ha, which corresponds to 'h' in the Greek. Removed accent from 'ύ'. Converted digamma 'F' to lowercase 'f'."
      }
    ]
    
    RULE 6 - Converting digamma:
    INPUT:
      linear_b: "wo-wo", 
      greek_cognate: "FόρFος", 
      transliteration: "worvos", 
      meaning: "border"
    
    OUTPUT:
    [
      {
        "linear_b": "wo-wo",
        "greek_cognates": ["fορfος"],
        "explanation": "Converted digamma 'F' to lowercase 'f'. Removed accent from 'ό'."
      }
    ]
    
    RULE 7 & 8 - Using only allowed characters:
    INPUT:
      linear_b: "pa-sa-ro", 
      greek_cognate: "ψάλιον (Y>ψ)", 
      transliteration: "psalion", 
      meaning: "chain"
    
    OUTPUT:
    [
      {
        "linear_b": "pa-sa-ro",
        "greek_cognates": ["ψαλιον"],
        "explanation": "Used only allowed characters. Removed accent from 'ά'. Ignored 'Y' as it's not in allowed characters."
      }
    ]
    
    RULE 9 - Handling disallowed characters:
    INPUT:
      linear_b: "qa-si-re-u", 
      greek_cognate: "κ/'ασιλεύς (>βασιλεύς)", 
      transliteration: "basileus", 
      meaning: "king"
    
    OUTPUT:
    [
      {
        "linear_b": "qa-si-re-u",
        "greek_cognates": ["βασιλευς"],
        "dubious": ["κασιλευς"],
        "explanation": "Removed disallowed characters '/' and '''. Removed accent from 'εύ'. Labeling κασιλευς as dubious because it is too modified compared to the effective greek cognate."
      }
    ]
    """
    
    # Additional complex examples
    additional_examples = ET.SubElement(prompt, "additional_examples")
    additional_examples.text = """
    ADDITIONAL COMPLEX EXAMPLES:

    EXAMPLE 1 - Multiple variants with complex cognates:
    INPUT:
      linear_b: "ko-ri-si-ja/ko-ri-si-jo", 
      greek_cognate: "Κορίνσια/Κορίνσιος(>Κορίνθια/Κορίνθιος)", 
      transliteration: "Korinsia/Korinsios (>Korinthia/Korinthios)", 
      meaning: "ethnic name of 'Koήnthos'"

    OUTPUT:
    [
      {
        "linear_b": "ko-ri-si-ja",
        "greek_cognates": ["κορινσια", "κορινθια"],
        "explanation": "First word from pair. Removed capital letter and accent from 'ί'. Included both forms, with 'νσ' and the later evolved 'νθ'."
      },
      {
        "linear_b": "ko-ri-si-jo",
        "greek_cognates": ["κορινσιος", "κορινθιος"],
        "explanation": "Second word from pair. Removed capital letter and accent from 'ί'. Included both masculine forms, with 'νσ' and the later evolved 'νθ'."
      }
    ]

    EXAMPLE 2 - Place name:
    INPUT:
      linear_b: "ku-ta-(i-)to", 
      greek_cognate: "Κύταιστος", 
      transliteration: "Kytaistos", 
      meaning: "place name"

    OUTPUT:
    [
      {
        "linear_b": "ku-ta-to",
        "greek_cognates": ["κυταιστος"],
        "explanation": "First variant without the optional 'i'. Removed capital letter and accent from 'ύ'."
      },
      {
        "linear_b": "ku-ta-i-to",
        "greek_cognates": ["κυταιστος"],
        "explanation": "Second variant with the optional 'i'. Removed capital letter and accent from 'ύ'."
      }
    ]

    EXAMPLE 3 - Personal name with digamma:
    INPUT:
      linear_b: "na-u-si-ke-re[-we]", 
      greek_cognate: "ΝαυσικλέFεις(>Ναυσικλής)", 
      transliteration: "Nausikleveis (>Νausikles)", 
      meaning: "personal name"

    OUTPUT:
    [
      {
        "linear_b": "na-u-si-ke-re",
        "greek_cognates": ["ναυσικλεfεις", "ναυσικλης"],
        "explanation": "First variant without the optional 'we'. Removed capital letter and accent from 'έ'. Converted digamma 'F' to lowercase 'f'. Included both forms."
      },
      {
        "linear_b": "na-u-si-ke-re-we",
        "greek_cognates": ["ναυσικλεfεις", "ναυσικλης"],
        "explanation": "Second variant with the optional 'we'. Removed capital letter and accent from 'έ'. Converted digamma 'F' to lowercase 'f'. Included both forms."
      }
    ]

    EXAMPLE 4 - Multiple variants with ha (aspiration):
    INPUT:
      linear_b: "o-/o-ha/o-da-ha/o-de-qa-ha", 
      greek_cognate: "ο-/οhά/οδάhα/οδετάhα", 
      transliteration: "ο-/oha/odaha/odetaha", 
      meaning: "introductory/prothetic world ='who, in this manner' (see also 'jo-')"

    OUTPUT:
    [
      {
        "linear_b": "o-",
        "greek_cognates": ["ο"],
        "explanation": "First form. No changes needed as it has no accents or special characters."
      },
      {
        "linear_b": "o-ha",
        "greek_cognates": ["οhα"],
        "explanation": "Second form with ha. Removed accent from 'ά'. Added 'h' due to the ha sign."
      },
      {
        "linear_b": "o-da-ha",
        "greek_cognates": ["οδαhα"],
        "explanation": "Third form with ha. Removed accent from 'ά'. Added 'h' due to the ha sign."
      },
      {
        "linear_b": "o-de-qa-ha",
        "greek_cognates": ["οδεταhα"],
        "explanation": "Fourth form with ha. Removed accent from 'ά'. Added 'h' due to the ha sign."
      }
    ]

    EXAMPLE 5 - Complex ethnic name with multiple variants:
    INPUT:
      linear_b: "pa-ki-ja-ni-ja/pa-ki-ja-ni-jo/pa-ki-ja-ni-jo-i/pa-ki-ja-ni-jo-jo", 
      greek_cognate: "Φασγιανία(ι)/Σφαγιανία(ι)/Φασγιανίοι/Σφαγιανίοι", 
      transliteration: "Phasgiania(i)/Sphagiania(i)/Phasgianioi/Sphagianioi", 
      meaning: "ethnic name of 'Phasgianai/Sphagianai'"

    OUTPUT:
    [
      {
        "linear_b": "pa-ki-ja-ni-ja",
        "greek_cognates": ["φασγιανια", "σφαγιανια", "φασγιανιαι", "σφαγιανιαι"],
        "explanation": "First form. Removed capital letter and accent from 'ί'. Included all variant forms with and without final 'ι', as well as both 'φ' and 'σφ' initial forms."
      },
      {
        "linear_b": "pa-ki-ja-ni-jo",
        "greek_cognates": ["φασγιανιοι", "σφαγιανιοι"],
        "explanation": "Second form. Removed capital letter and accent from 'ί'. Included both initial 'φ' and 'σφ' variants of the masculine form."
      },
      {
        "linear_b": "pa-ki-ja-ni-jo-i",
        "greek_cognates": ["φασγιανιοι", "σφαγιανιοι"],
        "explanation": "Third form with dative ending. Removed capital letter and accent from 'ί'. Included both initial 'φ' and 'σφ' variants."
      },
      {
        "linear_b": "pa-ki-ja-ni-jo-jo",
        "greek_cognates": ["φασγιανιοιο", "σφαγιανιοιο"],
        "explanation": "Fourth form with genitive ending. Removed capital letter and accent from 'ί'. Included both initial 'φ' and 'σφ' variants."
      }
    ]
    """

    
    prompt_str = ET.tostring(prompt, "utf-8").decode()
    
    # Using Gemini model to generate response
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel('models/gemini-2.0-flash')
    response = gemini_model.generate_content(prompt_str)
    
    # Extract and parse the JSON array
    pred = response.text.strip()
    json_start = pred.find('[')
    json_end = pred.rfind(']') + 1
    
    if json_start >= 0 and json_end > json_start:
        json_str = pred[json_start:json_end]
        try:
            return json.loads(json_str)  # Returns a list of dictionaries
        except json.JSONDecodeError:
            print("Error parsing JSON response")
            return []
    else:
        print("No valid JSON array found in response")
        return []

start_index = 819
prec_idx = 0
output_file = "./gemini_output.csv"

with open(output_file, mode='a', newline='', encoding='utf-8') as output_file:
    writer = None
    with open('dataset.csv', mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        # Convert the reader to a list of dicts
        data = [row for row in reader]
        header = list(data[0].keys())


        # Iterate through the matching keys starting from where we left off
        for i, info_dict in tqdm(enumerate(data[start_index:], start=start_index)):
            # Determine which API key to use
            if i % 300 == 0 and i != 0:
                time.sleep(60)
            idx = (i % (15 * len(api_keys))) // 15
            api_key = api_keys[idx]

            # Check if the API key has changed
            if idx != prec_idx:
                time.sleep(5)
            prec_idx = idx
            
            while True:
                try:
                    # Attempt to make the request and get the response
                    gemini_cognates = make_prompt(info_dict, api_key) #this returns list of JSON objects
                    for record in gemini_cognates:
                      if writer is None:
                          fieldnames = ["linear_b","greek_cognates","dubious", "explanation", "translation"]
                          writer = csv.DictWriter(output_file, fieldnames=fieldnames)
                          if output_file.tell() == 0:  # Write header only if file is empty
                              writer.writeheader()
                      record['greek_cognates'] = "|".join(record['greek_cognates'])
                      if "dubious" in record.keys():
                          record['dubious'] = "|".join(record['dubious'])
                      record['translation'] = info_dict['Translation (English)']
                      writer.writerow(record)
                      output_file.flush()

                      #Debug prints
                      print("INPUT WAS: ", info_dict)
                      print("WRITTEN OUTPUT: ", record)
                      #exit()
                    print("\n")
                    break
                except Exception as e:
                    print(f"Error occurred: {e}. Retrying in 65 seconds...")
                    time.sleep(65)
            
            
                
# pay attention to: 1. same LB word inserted twice 2. αγοραιοσ, (sigma ending the word)            
                
                
                
