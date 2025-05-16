import google.generativeai as genai
import csv
import xml.etree.ElementTree as ET
import json
import tqdm
import time
import os
from dotenv import load_dotenv


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
            if row[1] in cognates_dataset:
                cognates_dataset[row[1]]["lexicon_chadwick_ventris"] = row[2]
            else:
                cognates_dataset[row[1]] = {"lexicon_chadwick_ventris": row[2]}

with open('./additional_lexicon/gemini_output.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)
    for row in reader:
        if row:
            if "lexicon_tselentis" not in cognates_dataset[row[0]]:
                cognates_dataset[row[0]]["lexicon_tselentis"] = row[4]
            else:
                cognates_dataset[row[0]]["lexicon_tselentis"] += "/" + row[4]

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
    if "cognates" in info_dict:
        cognates = ET.SubElement(word_info, "cognates")
        cognates.text = "|".join(info_dict["cognates"])
    
    # Add lexicon entries if available
    if "lexicon_chadwick_ventris" in info_dict:
        cv_lexicon = ET.SubElement(word_info, "lexicon_chadwick_ventris")
        cv_lexicon.text = info_dict["lexicon_chadwick_ventris"]
        
    if "lexicon_tselentis" in info_dict:
        ts_lexicon = ET.SubElement(word_info, "lexicon_tselentis")
        ts_lexicon.text = info_dict["lexicon_tselentis"]
    
    # Create classification tasks section
    classification_tasks = ET.SubElement(prompt, "classification_tasks")
    classification_tasks.text = """
    CRITICAL: provide an answer IF AND ONLY IF YOU ARE COMPLETELY SURE DUE TO CERTAIN EVIDENCE!
    Please classify the given Linear B word according to the following tasks:
    
    1. Word Type: Determine if the word is an "anthroponym" (person name), "theonym" (deity name), "animal name", "toponym" (place name), or "common" word.
       Classes: -1 = uncertain/not applicable, 0 = anthroponym, 1 = animal name, 2 = theonym, 3 = toponym, 4 = common
    
    2. Gender: Determine the grammatical gender of the word.
       Classes: -1 = uncertain/not applicable, 0 = masculine, 1 = feminine, 2 = neuter
    
    3. Number: Determine the grammatical number of the word.
       Classes: -1 = uncertain/not applicable, 0 = singular, 1 = plural, 2 = dual
    
    4. Part of Speech: Determine the part of speech of the word.
       Classes: -1 = uncertain/not applicable, 0 = noun, 1 = verb, 2 = adjective, 3 = adverb
    
    5. Case: Determine the grammatical case of the word (if applicable).
       Classes: -1 = uncertain/not applicable, 0 = nominative/accusative/vocative, 1 = genitive, 2 = dative, 3 = instrumental
    
    For any classification where you are uncertain or the category is not applicable to the word, use -1.
    """
    
    # Create output format section
    output_format = ET.SubElement(prompt, "output_format")
    output_format.text = """Your response must be a JSON array containing exactly one object with the following structure:
    [
        {
            "word_type": integer (0-4 or -1),
            "gender": integer (0-2 or -1),
            "number": integer (0-2 or -1),
            "part_of_speech": integer (0-3 or -1),
            "case": integer (0-3 or -1),
            "confidence": float (0-1),
            "reasoning": "brief explanation of your classification decisions"
        }
    ]
    
    Do not include any additional explanation or text outside of this JSON array. The confidence field should reflect your overall confidence in the classifications."""
    
    # Create examples section with a few examples to help guide the model
    examples = ET.SubElement(prompt, "examples")
    examples.text = """Example 1:
    Word: a-to-ro-qo
    Cognates: ανθρωπος (human)
    Lexicon: anthropos - man, human
    Expected output:
    [
        {
            "word_type": 4,
            "gender": 0,
            "number": 0,
            "part_of_speech": 0,
            "case": 0,
            "confidence": 0.9,
            "reasoning": "This is the common noun 'anthropos' meaning 'man/human', masculine singular in nominative case."
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
            "gender": 1,
            "number": 0,
            "part_of_speech": 0,
            "case": 0,
            "confidence": 0.95,
            "reasoning": "This is 'potnia', a theonym/title for female deities, feminine singular in nominative case."
        }
    ]
    
    Example 3:
    Word: e-qe-ta
    Cognates: επετης (follower)
    Lexicon: hequetas - follower, companion
    Expected output:
    [
        {
            "word_type": 0,
            "gender": 0,
            "number": 0,
            "part_of_speech": 0,
            "case": 0,
            "confidence": 0.8,
            "reasoning": "This appears to be an anthroponym/title for a person (follower/companion), masculine singular in nominative case."
        }
    ]"""
    
    prompt_str = ET.tostring(prompt, "utf-8").decode()
    #print(prompt_str)

    # Using Gemini model to generate response
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash',
        generation_config=genai.types.GenerationConfig(
            temperature=0.0,     # Minima creatività
            top_p=1,             # Considera tutte le probabilità (nessun taglio)
            top_k=1,             # Scegli la parola più probabile
            max_output_tokens=512  # (Aumenta se ti serve output più lungo)
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
                        fieldnames = ["linear_b", "word_type", "gender", "number", "part_of_speech", "case", "confidence", "reasoning"]
                        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
                        if output_file.tell() == 0:  # Write header only if file is empty
                            writer.writeheader()

                    # Prepare the row to write
                    row = {
                        "linear_b": word,
                        "word_type": record['word_type'],
                        "gender": record['gender'],
                        "number": record['number'],
                        "part_of_speech": record['part_of_speech'],
                        "case": record['case'],
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