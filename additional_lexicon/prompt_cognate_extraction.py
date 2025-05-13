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
    
    # Historical context and linguistic principles
    principles = ET.SubElement(prompt, "rules")
    principles.text = """Linear B is a syllabic script used for writing Mycenaean Greek (1450-1200 BCE).
    When matching Linear B words with their Greek cognates, the following fundamental principles of historical linguistics must be observed:"""
    

    prompt = ET.tostring(prompt, "utf-8").decode()
    #print(prompt)

    # Using Gemini model to generate response
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel('models/gemini-2.0-flash')
    response = gemini_model.generate_content(prompt)
    pred = response.text.strip()
    pred = pred[pred.find('['):pred.rfind(']')+1]
    #print(json.loads(pred) )
    return json.loads(pred)  # This will return a list of dictionaries

input_file = 'dataset.csv'  # Output file to write cleaned data
with open(input_file, mode='r', newline='', encoding='utf-8') as infile: 
    reader = csv.reader(infile)
    header = next(reader)  # Read header
    print(header)
    data = list(reader)    # Convert the rest to a list

start_index = 0
prec_idx = 0
# Iterate through the matching keys starting from where we left off
for i, info in tqdm(enumerate(data[start_index:], start=start_index)):
    # Determine which API key to use
    #if i % 300 == 0:
    #    time.sleep(60)
    idx = (i % (15 * len(api_keys))) // 15
    api_key = api_keys[idx]
    print(api_key, info)

    info_dict = {header[i]: info[i] for i in range(len(header))}

    # Check if the API key has changed
    if idx != prec_idx:
        time.sleep(5)
    prec_idx = idx
    
    while True:
        try:
            # Attempt to make the request and get the response
            gemini_cognates = make_prompt(info_dict, api_key)
            break  # Exit the loop if successful
        except Exception as e:
            print(f"Error occurred: {e}. Retrying in 65 seconds...")
            time.sleep(65)
