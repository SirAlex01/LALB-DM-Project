import google.generativeai as genai
import csv
import xml.etree.ElementTree as ET
import json
import tqdm
import time
import os
from dotenv import load_dotenv
import re

cognates_dataset = {}
with open('cognates_final.cog', 'r', encoding='utf-8') as tsvfile:
    reader = csv.reader(tsvfile, delimiter='\t')
    next(reader)  # Skip header
    for row in reader:
        if row:  # Skip empty lines
            cognates_dataset[row[0]] = {"greek_cognates": row[1].split("|")}

with open('Linear B Lexicon.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # Skip header
    for row in reader:
        if row:  # Skip empty lines
            word = row[1].strip().lower().replace('"', '').replace("'", '').replace("to2", "tyo").replace("ro2", "ryo").replace("si2", "*64").replace("sa2", "*82").replace("ra3", "rai").replace("ra2", "rya").replace("pu2", "phu").replace("ta2","tya").replace("a3", "ai").replace("a2", "ha")
            if not (re.fullmatch(r"^(?:[a-z]+|\*\d{2})(?:-(?:[a-z]+|\*\d{2}))*$", word) is not None):
                print(f"Carattere non valido in {word}, it will not be included")
            else:
                if word in cognates_dataset:
                    cognates_dataset[word]["lexicon_chadwick_ventris"] = row[2]
                else:
                    cognates_dataset[word] = {"lexicon_chadwick_ventris": row[2]}

with open('./additional_lexicon/gemini_output.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)
    for row in reader:
        if row:
            word = row[0].strip().lower().replace("*66", "tya").replace("*71", "dwe")
            if not (re.fullmatch(r"^(?:[a-z]+|\*\d{2})(?:-(?:[a-z]+|\*\d{2}))*$", word) is not None):
                print(f"Carattere non valido in {word}, it will not be included")
            else:
                if "lexicon_tselentis" not in cognates_dataset[word]:
                    cognates_dataset[word]["lexicon_tselentis"] = row[4]
                else:
                    cognates_dataset[word]["lexicon_tselentis"] += "/" + row[4]

def make_prompt(info_dict, api_key):
    print(info_dict)
    # Create the root XML element
    prompt = ET.Element("root")
    
    # Create task section
    task = ET.SubElement(prompt, "task")
    task.text = "Analyze the given Linear B word and classify it according to linguistic categories"
    
    # Create context section
    context = ET.SubElement(prompt, "context")
    context.text = """Linear B was a syllabic script used for writing Mycenaean Greek, an early form of Greek spoken on Crete 
    and mainland Greece during the Late Bronze Age (1400-1200 BCE). This script was primarily used for administrative and 
    accounting purposes. You will analyze Linear B words to help train classifiers for linguistic analysis."""
    
    # Create word information section
    word_info = ET.SubElement(prompt, "word_info")
    
    # Add word element
    word = ET.SubElement(word_info, "word")
    word.text = info_dict["word"]
    
    # Add cognates if available
    if "greek_cognates" in info_dict:
        cognates = ET.SubElement(word_info, "greek_cognates")
        cognates.text = "|".join(info_dict["greek_cognates"])
        ET.SubElement(cognates, "greek_cognates_notice").text = """
        IMPORTANT: When provided, Greek cognates are critical evidence to help determine the word type, part of speech, and inflection class. Carefully analyze the Greek cognate's morphology, ending patterns, and meaning to inform your classification decisions.
        They are particularly important and you should USE THIS INFORMATION to PREDICT THE CORRECT INFLECTION also BASED ON THE DECLETION OF THE PROPOSED COGNATES.
        """

    # Add lexicon entries if available
    if "lexicon_chadwick_ventris" in info_dict:
        cv_lexicon = ET.SubElement(word_info, "lexicon_chadwick_ventris")
        cv_lexicon.text = info_dict["lexicon_chadwick_ventris"]
        
    if "lexicon_tselentis" in info_dict:
        ts_lexicon = ET.SubElement(word_info, "lexicon_tselentis")
        ts_lexicon.text = info_dict["lexicon_tselentis"]
    
    # Create classification tasks section
    # After correction: THE FIRST 3 word_type FIELDS WERE AGGREGATED, THE REMAINING ONES SCALED BY 2
    classification_tasks = ET.SubElement(prompt, "classification_tasks")
    classification_tasks.text = """
    CRITICAL: provide an answer IF AND ONLY IF YOU ARE COMPLETELY SURE DUE TO CERTAIN EVIDENCE! TAKE INTO ACCOUNT THE GIVEN DECLETION TABLES FOR ADJECTIVES AND NOUNS INFLECTIONS!
    Please classify the given Linear B word according to the following tasks:
    
    1. Word Type: Determine if the word is an "anthroponym" (person name), "animal name", "theonym" (deity name), "toponym" (place name), "ethnonym" (ethnic group name), or "common" word.
       Classes: -1 = uncertain/not applicable, 0 = anthroponym, 1 = animal name, 2 = theonym, 3 = toponym, 4 = ethnonym, 5 = common
    
    2. Part of Speech: Determine the part of speech of the word.
       Classes: -1 = uncertain/not applicable, 0 = noun, 1 = verb, 2 = adjective, 3 = adverb
    
    3. Inflection: Determine the inflection class of the word.
       For nouns AND adjectives: -1 = uncertain/not applicable, 0 = thematic in -o, 1 = thematic in -a, 2 = athematic
       For verbs and adverbs: -1 (not applicable)
       Note: For adjectives, use the same inflection classes as nouns based on their endings.
    
    Note on Participles: When analyzing participles (verbal adjectives), always classify them as ADJECTIVES (part_of_speech = 2), not as verbs. For participles, determine their inflection class using the same criteria as for nouns and adjectives (0 = thematic in -o, 1 = thematic in -a, 2 = athematic).
    TAKE INTO ACCOUNT THE FOLLOWING: The provided declension table contains trailing suffixes, but being Linear B a syllabic language, they can be preceeded by an arbitrary consonant and be insterted in a syllable.

    """
    
    # Create declension table section
    nouns_section = ET.SubElement(prompt, "nouns")
    decl_table = ET.SubElement(nouns_section, "declension_table").text = '''
    This is the an exaustive table with Mycenean linear b declensions suffixes attested in the documents.
    You MUST use this table to correctly classify the inflection of the world. It is based on ancient greek decletions: the first two coluns correspond to Ancient greek's second decletion, the second two columns correspond to the first decletions, while the last two correspond to the third decletion in ancient greek.
    The same suffixes are also used for the adjectives of the first class (the first four columns), and for those of the second class (the last two columns).
    | Number | Case       | Fless. Tem. (M.) | Fless. Tem. (N.) | Fless. in -a (M.) | Fless. in -a (F.) | Fless. atem. (M./F.)  | Fless. atem. (N.) (?)              | 
    | ------ | ---------- | -----------      | -----------      | ----------------- | ----------------- | --------------        | --------------                     |
    | Sing.  | Nominative | -o               | -o               | -a                | -a                | variable              | variable                           |
    |        | Genitive   | -ojo             | -ojo             | -ao               | -a                | -o                    | -o                                 |
    |        | Dative     | -o               | -o               | -a                | -a                | -e/-i                 | -e/-i                              |
    |        | Accusative | -o               | -o               | -a                | -a                | -a                    | variable (identical to nominative) |
    | Plural | Nominative | -o/-oi           | -a               | -a                | -a                | -e                    | -a                                 |
    |        | Genitive   | -o               | -o               | -ao               | -ao               | -o                    | -o                                 |
    |        | Dative     | -oi              | -oi              | -ai               | -ai               | -si/-ti               | -si/-ti                            |
    |        | Accusative | -o               | -a               | -a                | -a                | -a/-e                 | -a                                 |
    
    PAY ATTENTION TO ATHEMATIC'S GENITIVE -o SUFFIX AND NOMINATIVE (FOR NEUTER WORDS) AND ACCUSATIVE -a SUFFIX: THEY ARE VERY SIMILAR TO THEMATIC TERMS' SUFFIXES AND YOU NEED TO LEVERAGE THE PROVIDED ANCIENT GREEK COGNATES TO BREAK TIES.

    '''

    # old table commented out
    '''
    # Declension table data
    rows = [
        ("Singular", "Nominative", "-o", "-o", "-a", "-a", "variable", "variable"),
        ("Singular", "Genitive", "-ojo", "-ojo", "-ao", "-a", "-o", "-o"),
        ("Singular", "Dative", "-o", "-o", "-a", "-a", "-e/-i", "-e/-i"),
        ("Singular", "Accusative", "-o", "-o", "-a", "-a", "-a", "variable (identical to nominative)"),
        ("Plural", "Nominative", "-o/-oi", "-a", "-a", "-a", "-e", "-a"),
        ("Plural", "Genitive", "-o", "-o", "-ao", "-ao", "-o", "-o"),
        ("Plural", "Dative", "-oi", "-oi", "-ai", "-ai", "-si/-ti", "-si/-ti"),
        ("Plural", "Accusative", "-o", "-a", "-a", "-a", "-a/-e", "-a"),
    ]

    # Add each row to the XML
    for number, case, tem_m, tem_n, a_m, a_f, athem, athem_n in rows:
        row = ET.SubElement(decl_table, "row")
        ET.SubElement(row, "number").text = number
        ET.SubElement(row, "case").text = case
        ET.SubElement(row, "thematic_o_masculine_feminine").text = tem_m
        ET.SubElement(row, "thematic_o_neuter").text = tem_n
        ET.SubElement(row, "thematic_a_masculine").text = a_m
        ET.SubElement(row, "thematic_a_feminine").text = a_f
        ET.SubElement(row, "athematic_masculine_feminine").text = athem
        ET.SubElement(row, "athematic_neuter").text = athem
    '''

    verbs_section = ET.SubElement(prompt, "verbs")
    rules = {
        "3rd singular": "last syllabogram ending with vowel -e",
        "3rd plural": "last syllabogram is -si",
        "infinite": "last syllabogram ending with vowel e (optionally another syllabogram -e appears at the end)",
        "participle": "active -> terminates with -o (singular -ων ancient greek suffix, other suffixes follow athematic nouns, e.g. -o-te like i-jo-te -> ιοντες, from ειμι)",
        "participle": "medium/passive -> terminates with -me-no/-me-na suffixes (ancient greek -μενος/-μενη/-μενον suffixes)"
    }
    for rule_key, rule_text in rules.items():
        ET.SubElement(verbs_section, rule_key).text = rule_text

    adjectives_section = ET.SubElement(prompt, "adjectives")
    rules = {
        "thematic adjectives": "thematic adjectives have same behavior as thematic nouns",
        "athematic adjectives": "athematic adjectives have same behavior as athematic nouns (variable nominative and same decletions)"
    }
    for rule_key, rule_text in rules.items():
        ET.SubElement(adjectives_section, rule_key).text = rule_text
        

    # Create output format section
    output_format = ET.SubElement(prompt, "output_format")
    output_format.text = """Your response must be a JSON array containing exactly one object with the following structure:
    [
        {
            "word_type": integer (0-5 or -1),
            "part_of_speech": integer (0-3 or -1),
            "inflection": integer (0-2 or -1),
            "confidence": float (0-1),
            "reasoning": "brief explanation of your classification decisions"
        }
    ]
    
    Do not include any additional explanation or text outside of this JSON array. The confidence field should reflect your overall confidence in the classifications."""
    
    # Create suffixes section to inform about elements that should be ignored
    suffixes = ET.SubElement(prompt, "suffixes_to_ignore")
    suffixes.text = """The following suffixes should be ignored when analyzing Linear B words, as they do not provide relevant information for the classification tasks. When you encounter these suffixes, consider the word without them for classification purposes:

    1. -qe: conjunction suffix meaning "and" (equivalent to Latin -que)
    2. -te: ablative suffix meaning "away from a place" (equivalent to Greek -θεν)
    3. -de: can be either:
       - Negative prefix meaning "not, on the other side"
       - Allative/demonstrative suffix (equivalent to Greek -δε)
    4. -pi: instrumental/locative suffix

    Example: If analyzing "ko-to-na-qe" (and plot of land), you should classify "ko-to-na" (plot of land) ignoring the -qe conjunction suffix.
    """

    # Create examples section with more meaningful examples
    examples = ET.SubElement(prompt, "examples")
    examples.text = """Example 1:
    Word: a-to-ro-qo
    Cognates: ανθρωπος (human)
    Lexicon: anthropos - man, human
    Expected output:
    [
        {
            "word_type": 5,
            "part_of_speech": 0,
            "inflection": 0,
            "confidence": 0.9,
            "reasoning": "This is the common noun 'anthropos' meaning 'man/human', a thematic noun in -o."
        }
    ]
    
    Example 2:
    Word: po-ti-ni-ja
    Cognates: ποτνια (mistress, lady)
    Lexicon: potnia - mistress, lady, female deity title
    Expected output:
    [
        {
            "word_type": 2,
            "part_of_speech": 0,
            "inflection": 1,
            "confidence": 0.95,
            "reasoning": "This is 'potnia', a theonym/title for female deities, a thematic noun in -a."
        }
    ]
    
    Example 3:
    Word: e-qe-ta
    Cognates: επετης (follower)
    Lexicon: hequetas - follower, companion
    Expected output:
    [
        {
            "word_type": 5,
            "part_of_speech": 0,
            "inflection": 1,
            "confidence": 0.8,
            "reasoning": "This is an title for a person (follower/companion), a thematic noun in -a."
        }
    ]
    
    Example 4:
    Word: pa-i-to
    Cognates: Φαιστος (Phaistos)
    Lexicon: Phaistos - name of a Minoan palace/city
    Expected output:
    [
        {
            "word_type": 3,
            "part_of_speech": 0,
            "inflection": 0,
            "confidence": 0.9,
            "reasoning": "This is 'Phaistos', a toponym (place name), a thematic noun in -o."
        }
    ]
    
    Example 5:
    Word: e-ko-me-na
    Cognates: εχομενα (being held)
    Lexicon: ekhomena - being held, possessed
    Expected output:
    [
        {
            "word_type": 5,
            "part_of_speech": 2,
            "inflection": 1,
            "confidence": 0.85,
            "reasoning": "This is a participle 'ekhomena' (being held), which is classified as an adjective with the -me-na ending typical of passive participles. The ending indicates thematic in -a inflection."
        }
    ]
    
    Example 6:
    Word: e-re-u-te-ro
    Cognates: ελευθερος (free)
    Lexicon: eleutheros - free, unencumbered
    Expected output:
    [
        {
            "word_type": 5,
            "part_of_speech": 2,
            "inflection": 0,
            "confidence": 0.9,
            "reasoning": "This is the common adjective 'eleutheros' meaning 'free', a thematic adjective in -o."
        }
    ]
    
    Example 7:
    Word: do-e-ro
    Cognates: δουλος (slave)
    Lexicon: doelos - slave, servant
    Expected output:
    [
        {
            "word_type": 5,
            "part_of_speech": 0,
            "inflection": 0,
            "confidence": 0.95,
            "reasoning": "This is the common noun 'doelos' meaning 'slave', a thematic noun in -o."
        }
    ]
    
    Example 8:
    Word: a-ke-re-u
    Cognates: αγρευς (hunter)
    Lexicon: agreus - hunter, collector
    Expected output:
    [
        {
            "word_type": 0,
            "part_of_speech": 0,
            "inflection": 2,
            "confidence": 0.8,
            "reasoning": "This is an anthroponym 'agreus' meaning 'hunter', an athematic noun as indicated by the -u ending."
        }
    ]
    
    Example 9:
    Word: ka-ke-u
    Cognates: χαλκευς (bronze-smith)
    Lexicon: khalkeus - bronze-smith, metalworker
    Expected output:
    [
        {
            "word_type": 0,
            "part_of_speech": 0,
            "inflection": 2,
            "confidence": 0.9,
            "reasoning": "This is an anthroponym 'khalkeus' meaning 'bronze-smith', an athematic noun as indicated by the -u ending."
        }
    ]
    
    Example 10:
    Word: di-we
    Cognates: Διος/Ζευς (Zeus, dative case)
    Lexicon: dative form of Zeus
    Expected output:
    [
        {
            "word_type": 2,
            "part_of_speech": 0,
            "inflection": 2,
            "confidence": 0.95,
            "reasoning": "This is the dative form of Zeus (theonym), an athematic noun showing the characteristic -e ending for athematic datives."
        }
    ]
    
    Example 11:
    Word: a-ka-so-ne 
    Cognates: αξονες (axles)
    Lexicon: axones - axles (wheels)
    Expected output:
    [
        {
            "word_type": 5,
            "part_of_speech": 0,
            "inflection": 2,
            "confidence": 0.85,
            "reasoning": "This is the common noun 'axones' meaning 'axles', an athematic noun."
        }
    ]
    
    Example 12:
    Word: e-ko-si
    Cognates: εχουσι (they have)
    Lexicon: ekhousi - they have/hold
    Expected output:
    [
        {
            "word_type": 5,
            "part_of_speech": 1,
            "inflection": -1,
            "confidence": 0.9,
            "reasoning": "This is a verb form 'ekhousi' (they have), recognizable as 3rd person plural by the -si ending."
        }
    ]"""
    check = ET.SubElement(prompt, "check").text = """
    AFTER MAKING YOUR DECISION, PERFORM THE FOLLOWING CONSISTENCY CHECKS:
    1. If you classified a word as a verb or adverb (part_of_speech = 1 or 3), confirm that inflection = -1
    2. If you identified a participle, verify that you classified it as an adjective (part_of_speech = 2)
    3. Ensure your word_type classification is consistent with the meaning of the word
    4. Confirm that the inflection class matches the actual ending pattern of the word
    5. Check that your reasoning fully explains and supports all classification decisions
    6. Verify that there are no contradictions between your classifications and your reasoning
    7. Check that the inflection is compatible with the ones of the greek cognates
    8. REMEMBER THE FOLLOWING, WHICH IS A CRITICAL PROBLEM: PAY ATTENTION TO ATHEMATIC'S GENITIVE -o SUFFIX AND NOMINATIVE (FOR NEUTER WORDS) AND ACCUSATIVE -a SUFFIX: THEY ARE VERY SIMILAR TO THEMATIC TERMS' SUFFIXES AND YOU NEED TO LEVERAGE THE PROVIDED ANCIENT GREEK COGNATES TO BREAK TIES. FOR ANY MISTAKE OF THIS KIND AN INNOCENT KID WILL DIE.

    REVISE ANY INCONSISTENCIES BEFORE SUBMITTING YOUR FINAL ANSWER.
    """
    prompt_str = ET.tostring(prompt, "utf-8").decode()
    
    #print(prompt_str)
    #exit()
    
    # Using Gemini model to generate response
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        generation_config=genai.types.GenerationConfig(
            temperature=0.0,     # Minimal creativity
            top_p=1,             # Consider all probabilities (no cutting)
            top_k=1,             # Choose the most probable word
            max_output_tokens=512  # (Increase if you need longer output)
        )
    )
    
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


output_file = "classifiers_dataset.csv"
prec_idx = 0
load_dotenv()

# Retrieve the API key

api_keys = [os.getenv("GOOGLE_API_KEY_1"), os.getenv("GOOGLE_API_KEY_2"), os.getenv("GOOGLE_API_KEY_3"), os.getenv("GOOGLE_API_KEY_4"), os.getenv("GOOGLE_API_KEY_5")
            , os.getenv("GOOGLE_API_KEY_6"), os.getenv("GOOGLE_API_KEY_7"), os.getenv("GOOGLE_API_KEY_8"), os.getenv("GOOGLE_API_KEY_9")]

with open(output_file, mode='w', newline='', encoding='utf-8') as output_file:
    writer = None
    for i, (word, info_dict) in enumerate(cognates_dataset.items()):
        info_dict["word"] = word

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
                gemini_answer = make_prompt(info_dict, api_key)  # this returns list of JSON objects

                for record in gemini_answer:
                    if writer is None:
                        fieldnames = ["linear_b", "word_type", "part_of_speech", "inflection", "confidence", "reasoning"]
                        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
                        if output_file.tell() == 0:  # Write header only if file is empty
                            writer.writeheader()

                    # Prepare the row to write
                    row = {
                        "linear_b": word,
                        "word_type": record['word_type'],
                        "part_of_speech": record['part_of_speech'],
                        "inflection": record['inflection'],
                        "confidence": record['confidence'],
                        "reasoning": record['reasoning']
                    }

                    writer.writerow(row)
                    output_file.flush()

                    # Debug prints
                    print("INPUT WAS: ", info_dict)
                    print("WRITTEN OUTPUT: ", row)

                print("\n")
                break
            except Exception as e:
                print(f"Error occurred: {e}. Retrying in 65 seconds...")
                time.sleep(65)