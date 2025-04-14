import csv
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import os
import google.generativeai as genai
import time
from tqdm import tqdm
# recall proper names types: anthroponym, ethnonym, phytonym, toponym, patronymic, theonym


# Load environment variables from .env file
load_dotenv()

# Retrieve the API key

api_keys = [os.getenv("GOOGLE_API_KEY_1"), os.getenv("GOOGLE_API_KEY_2"), os.getenv("GOOGLE_API_KEY_3"), os.getenv("GOOGLE_API_KEY_4"), os.getenv("GOOGLE_API_KEY_5")
            , os.getenv("GOOGLE_API_KEY_6"), os.getenv("GOOGLE_API_KEY_7"), os.getenv("GOOGLE_API_KEY_8"), os.getenv("GOOGLE_API_KEY_9")]



def latinize_greek(greek_file, latinized_greek_file):
    # Greek-to-Latin character mapping dictionary
    greek_to_latin = {
        'α': 'a', 'β': 'q', 'γ': 'k', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'e', 'θ': 't',
        'ι': 'i', 'κ': 'k', 'λ': 'r', 'μ': 'm', 'ν': 'n', 'ξ': 'ks', 'ο': 'o', 'π': '*',
        'ρ': 'r', 'σ': 's', 'τ': 't', 'υ': 'u', 'φ': 'p', 'χ': 'k', 'ψ': 'ps', 'ω': 'o', 'ς': 's',
        #'ά': 'á', 'έ': 'é', 'ή': 'í', 'ί': 'í', 'ό': 'ó', 'ύ': 'ý', 'ώ': 'ó', 'ς': 's', # Special characters
        #'ϊ': 'i', 'ΰ': 'y', 'ϋ': 'y', 'ΐ': 'i'
    }
    
    # Open the Greek file for reading and the output file for writing the Latinized words
    with open(greek_file, 'r', encoding='utf-8') as infile, open(latinized_greek_file, 'w', encoding='utf-8') as outfile:
        # Skip the header (if present)
        header = infile.readline()
        
        # Write the header for the output file
        outfile.write("Latinized Greek\t Greek\n")
        
        # Process each line in the Greek file
        for line in infile:
            # Remove any leading/trailing whitespace (including newline characters)
            greek_word = line.strip()
            
            # Latinize the Greek word by replacing each character
            latinized_word = ''.join([greek_to_latin.get(char, char) for char in greek_word])
            
            # Write the Latinized word to the output file
            outfile.write(f"{latinized_word}\t{greek_word}\n")

def collect_lin_b_words(linear_b_file):
    words = {}
    with open(linear_b_file, 'r', encoding='utf-8') as f:
        # Skip the header (if present)
        header = f.readline()
        for i, r in enumerate(f):
            # DEBUG
            #if i < 560: continue
            #if i > 800: break
            
            word, valid = r.strip().split("\t")
            words[word] = {"valid": bool(int(valid)), "cognates":[]}
    return words

def collect_greek_words(latinized_greek_file):
    words = {}
    with open(latinized_greek_file, 'r', encoding='utf-8') as f:
        # Skip the header (if present)
        header = f.readline()
        for r in f:
            ws = r.strip().split("\t")
            words[ws[0]] = ws[1]
    return words

def match(lin_b_words, greek_words):
    for lb in tqdm(lin_b_words.keys()):
        # consonant threshold of edit distance
        lb_list = lb.split("-")
        for g in greek_words.keys():
            
            g_list = list(g)
            i = 0
            j = 0
            dist = 0
            skipped = 0
            skipped_consecutive = 0
            max_sc = 0
            wrong_syl = False
            skipped_syls = []
            while i < len(lb_list) and j < len(g_list):
                #print(i, j, lb_list[i:], g_list[j:], skipped, skipped_consecutive, max_sc)
                old_i = i
                old_j = j
                lb_syl = lb_list[i]
                g_char = g_list[j]
                if len(lb_syl) == 1:
                    # matched
                    #print(g_char, lb_syl)
                    if g_char == lb_syl:
                        skipped_consecutive = 0
                        i += 1
                        j += 1
                    else:
                        skipped += 1
                        skipped_consecutive += 1
                        j += 1
                elif len(lb_syl) == 2:
                    cons = lb_syl[0]
                    if cons == "k":
                        # check παγχυλιων-like stuff
                        double_gut = j + 2 < len(g_list) and "".join(g_list[j+1:j+3]) == lb_syl

                        # matched
                        if g_char == "k" and not double_gut:
                            skipped_consecutive = 0
                            # matched ks
                            if j+1 < len(g_list) and g_list[j+1] == "s" and i < len(lb_list) - 1:
                                next_syl = lb_list[i+1]
                                if next_syl[0] == "s":
                                    i += 2
                                    j += 2
                                    # matching vowel after s
                                    if j < len(g_list) and next_syl[1] == g_list[j]:
                                        j += 1
                                else:
                                    i += 1
                                    j += 1
                                    if j < len(g_list) and lb_syl[1] == g_list[j]:
                                        j += 1
                            else:
                                i += 1
                                j += 1
                                if j < len(g_list) and lb_syl[1] == g_list[j]:
                                    j += 1
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1

                    if cons == "p":
                        # matching ps
                        if g_char == "p" or g_char == "*":
                            skipped_consecutive = 0
                            # matched ks
                            if j+1 < len(g_list) and g_list[j+1] == "s" and i < len(lb_list) - 1:
                                next_syl = lb_list[i+1]
                                if next_syl[0] == "s":
                                    i += 2
                                    j += 2
                                    # matching vowel after s
                                    if j < len(g_list) and next_syl[1] == g_list[j]:
                                        j += 1
                                else:
                                    i += 1
                                    j += 1
                                    if j < len(g_list) and lb_syl[1] == g_list[j]:
                                        j += 1
                            else:
                                i += 1
                                j += 1
                                if j < len(g_list) and lb_syl[1] == g_list[j]:
                                    j += 1
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1

                    if cons == "q":
                        if g_char == "q" or g_char == "*" or g_char == "k":
                            skipped_consecutive = 0
                            i += 1
                            j += 1
                            if j < len(g_list) and lb_syl[1] == g_list[j]:
                                j += 1
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1

                    if cons == "r":
                        if g_char == "r":
                            skipped_consecutive = 0
                            i += 1
                            j += 1
                            if j < len(g_list) and lb_syl[1] == g_list[j]:
                                j += 1
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1
                    if cons == "s":
                        if g_char == "s":
                            skipped_consecutive = 0
                            i += 1
                            j += 1
                            if j < len(g_list) and lb_syl[1] == g_list[j]:
                                j += 1
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1
                    if cons == "t":
                        if g_char == "t":
                            skipped_consecutive = 0
                            i += 1
                            j += 1
                            if j < len(g_list) and lb_syl[1] == g_list[j]:
                                j += 1
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1
                    if cons == "d":
                        if g_char == "d":
                            skipped_consecutive = 0
                            i += 1
                            j += 1
                            if j < len(g_list) and lb_syl[1] == g_list[j]:
                                j += 1
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1
                    if cons == "m":
                        if g_char == "m":
                            skipped_consecutive = 0
                            i += 1
                            j += 1
                            if j < len(g_list) and lb_syl[1] == g_list[j]:
                                j += 1
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1
                    if cons == "n":
                        if g_char == "n":
                            skipped_consecutive = 0
                            i += 1
                            j += 1
                            if j < len(g_list) and lb_syl[1] == g_list[j]:
                                j += 1
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1
                    if cons == "z":
                        if g_char == "z":
                            skipped_consecutive = 0
                            i += 1
                            j += 1
                            if j < len(g_list) and lb_syl[1] == g_list[j]:
                                j += 1
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1
                    if cons == "j":
                        if g_char == "i":
                            skipped_consecutive = 0
                            i += 1
                            j += 1
                            if j < len(g_list) and lb_syl[1] == g_list[j]:
                                j += 1
                        elif g_char == lb_syl[1]:
                            skipped_consecutive = 0
                            i += 1
                            j += 1
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1
                    if cons == "w":
                        # check only the vowel
                        if g_char == lb_syl[1]:
                            g_list = g_list[:j] + ["f"] + g_list[j:]
                            skipped_consecutive = 0
                            i += 1
                            j += 2
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1


                    if cons == "h":
                        if g_char == lb_syl[1]:
                            g_list = g_list[:j] + ["h"] + g_list[j:]
                            skipped_consecutive = 0
                            i += 1
                            j += 2

                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1

                    if cons == "a":
                        if j+1 < len(g_list) and g_char == "a" and g_list[j+1] == lb_syl[1]:
                            skipped_consecutive = 0
                            i += 1
                            j += 2
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1
                    
                    # matching occurred
                    if old_i != len(lb_list)-1 and (lb_list[old_i][0] == g_list[old_j] or (lb_list[old_i][0] == "p" and g_list[old_j] == "*")):
                        if old_j + 1 < len(g_list) and g_list[old_j+1] != lb_list[old_i][1] and g_list[old_j+1] in "aeiou":
                            # salva le occorrenze del dittongo "ou"
                            if old_j + 2 < len(g_list) and lb_list[old_i][1] == "u" and g_list[old_j+1] == "o" and g_list[old_j+2] == "u":
                                j += 2
                            # WRONG SYLLABOGRAM
                            else:
                                wrong_syl = True
                                break

                if len(lb_syl) == 3:
                    if lb_syl == "phu":
                        if j + 1 < len(g_list) and g_char == "p" and g_list[j+1] == "u":
                            skipped_consecutive = 0
                            i += 1
                            j += 2
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1
                    elif lb_syl == "rya" or lb_syl == "tya" or lb_syl == "ryo":
                        # epsilon di appoggio
                        cond1 = j + 3 < len(g_list) and g_list[j+1] == "e" and g_list[j+2] == "i" and g_list[j+3] == lb_syl[-1]
                        cond2 = j + 2 < len(g_list) and g_list[j+1] == "i" and g_list[j+2] == lb_syl[-1]

                        if g_char == lb_syl[0] and (cond1 or cond2):
                            skipped_consecutive = 0
                            i += 1
                            j += 4 if cond1 else 3
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1
                    elif lb_syl == "pte":
                        if j+2 < len(g_list) and (g_char == "p" or g_char == "*") and g_list[j+1] == lb_syl[1] and g_list[j+2] == lb_syl[2]:
                            skipped_consecutive = 0
                            i += 1
                            j += 3
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1

                    elif lb_syl == "rai":
                        cond1 = j + 3 < len(g_list) and g_list[j+1] == "e" and g_list[j+2] == lb_syl[-2] and g_list[j+3] == lb_syl[-1]
                        cond2 = j + 2 < len(g_list) and g_list[j+1] == lb_syl[-2] and g_list[j+2] == lb_syl[-1]
                        if g_char == lb_syl[0] and (cond1 or cond2):
                            skipped_consecutive = 0
                            i += 1
                            j += 4 if cond1 else 3
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1
                    elif lb_syl in ["twe", "two", "dwe", "dwo", "nwa"]:
                        if j+1 < len(g_list) and lb_syl[0] == g_char and g_list[j+1] == lb_syl[1]:
                            g_list = g_list[:j+1] + ["f"] + g_list[j+1:]
                            skipped_consecutive = 0
                            i += 1
                            j += 3
                        else:
                            j += 1
                            skipped += 1
                            skipped_consecutive += 1
                    elif lb_syl.startswith("*"):
                        # unknown syllabogram how am I supposed to deal with this shit at all?
                        i += 1
                        j += 2

                max_sc = max(max_sc, skipped_consecutive)
                if skipped_consecutive == 2:
                    skipped_syls.append("".join(g_list[j-2:j]))

            # liquid consonants can fly!
            if max_sc == 2 and len(skipped_syls) == 1:
                if skipped_syls[0][0] == "r":
                    max_sc = 0

            # constraints: mapping succesful, first letter matches, do not add too much letters
            begin_with_same = lb[0] == g[0] or (lb[0] == "p" and g_list[0] == "*") or (lb[0] == "t" and g_list[0] == "s" and g_list[1] == "t") or \
                              (lb[0] == "w" and g_list[0] == "f") or  (lb[0] == "q" and (g_list[0] == "k" or g_list[0] == "*")) or \
                              (lb[0] == "p" and g_list[0] == "s" and g_list[1] == "p")

            if i >= len(lb_list) - 1 and j >= len(g) - 3 and skipped < 4 and begin_with_same and max_sc <= 2 and not wrong_syl:
                if (len(lb_list) <= 3 and skipped <= 2 and j >= len(g) - 2 and max_sc < 2) or len(lb_list) > 3:
                    gr = list(greek_words[g])
                    if len(greek_words[g]) < len(g_list):
                        subs = [(i, j) for i, j in enumerate(g_list) if j == "f" or j == "h"]
                        for s in subs:
                            i, j = s
                            gr.insert(i, j)
                    lin_b_words[lb]["cognates"].append(("".join(gr), i/len(lb_list)))
            #check compatibility
                
                
    return lin_b_words

# Specify your input and output file names
linear_b_file = "linb_words.tsv"
greek_file = "latinized_homeric_greek_words.tsv"


lin_b_words = collect_lin_b_words(linear_b_file)
greek_words = collect_greek_words(greek_file)

#matching = match({"a-da-wa-si-jo":{"valid":True, "cognates":[]}}, {"a*odrfas": ""})
matching = match(lin_b_words, greek_words)
for k in matching.keys():
    matching[k]["cognates"] = sorted(matching[k]["cognates"], key = lambda x:x[1], reverse=True)

print(matching)

# Open and process the CSV file
with open("Linear B Lexicon.csv", newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    
    for row in reader:
        transcription = row["transcription"]
        transcription = transcription.replace("pu2","phu").replace("ro2","ryo").replace("ra2", "rya").replace("ra3", "rai").replace("ta2", "tya").replace("a2","ha").replace("a3","ai")

        #assert transcription in matching.keys()
        if transcription in matching:
            matching[transcription]["definition"] = row["definition"]

with open("converted_linear_b-greek.cog", newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile, delimiter="\t")
    
    for row in reader:
        word = row["converted_linear_b"]
        #assert word in matching.keys()
        if word in matching:
            matching[word]["cognates"] = [(r, 1.0) for r in row["greek"].split("|")]



def make_prompt(word, info_dict, api_key):
    # Create the root XML element
    prompt = ET.Element("root")
    instr = ET.SubElement(prompt, "task_instructions")
    ET.SubElement(instr, "task_description").text = """ We are trying to find the cognates for our Linear B words and try to train a model which automatically matches them to their Ancient Greek correspondances. 
    Help us in this task by considering all the information we provide."""

    rules = ["THIS IS THE MOST IMPORTANT RULE: DO NOT USE ANY OTHER LATIN CHARACTER IN YOUR OUTPUT EXCEPT FOR f AND h UNDER RULES 2. AND 3.! THIS IS YOU ALLOWED CHARSET: fhαβγδεζηθικλμνξοπρςστυφχψω",
             "Try to reconstruct the sequence yourself, especially for toponyms, antroponyms and patronymics, where Iliad and Odissey (our ancient greek sources) may not have any correspondance.",
             "Whenever you find a linear b syllabogram with ha, insert an h in the corresponding position also in the ancient greek sequence.",
             "Whenever you find a linear b syllabogram containing \"digamma\" (w), insert in the correct position an f to account for its presence in the original ancient greek root.",
             "Try to abstract the rules cited in the definition field. However, do not blindly use the suggestions provided, but always start from the linear B sequence, especially for proper names.",
             "Output simply one or more cognates, separated by \",\", if valid is True. Otherwise, only a single option.",
             "For words which are not proper names, try to match them to existing ancient greek words, with a comparable logical function in the sentence.",
             "For proper names like antroponyms, toponyms, and patronymic try to reconstruct the existing word with a transliteration. They are not likely present in our source. DO NOT USE VERBS/ADVERBS FOR THEM!",
             "IF A WORD IS NOT VALID OUTPUT ONLY ONE MATCH!"
             ]
    for i, r in enumerate(rules):
        ET.SubElement(instr, f"rule_{i}").text = rules[i]

    mapping = ET.SubElement(prompt, "known_mapping")
    lin_b_cons = list("kpqrstdmnzjwhy")+["ph"]
    correspondances = {"k": ["κ", "χ", "γ", "ξ"],
                       "p": ["π", "φ", "ψ"],
                       "q": ["β", "π", "κ", "γ", "ψ", "ξ"],
                       "r": ["ρ", "λ"],
                       "d": ["δ"],
                       "t": ["τ", "θ"],
                       "m": ["μ"],
                       "n": ["ν"],
                       "z": ["ζ"],
                       "j": ["ι"],
                       "w": ["f"],
                       "h": ["h"],
                       "ph": ["φ"],
                       "y": ["ι", "ει"],
                       "s": ["σ","ς"]
                       }
    notes = {
        "k": "no difference in linear B between κ, χ, and γ. When it corresponds to ξ the syllabogram is usually BUT NOT ALWAYS followed by a syllabogram starting with s.",
        "p": "corresponds to π and φ. When it corresponds to ψ the syllabogram is usually BUT NOT ALWAYS followed by a syllabogram starting with s.",
        "q": "usually corresponds to β and π. It may also correspond to κ or γ or even ψ or ξ when followed by a syllabogram starting with s. Evaluate it VERY CAREFULLY due to the high number of possible correspondances.",
        "r": "corresponds to liquid consonants ρ and λ. Be careful because IN LINEAR B THE SYLLABLES CONTAINING LIQUID CONSONANTS ARE OFTEN OMITTED (especially in certain position which you may check, as Chadwick explained).",
        "j": "this is the archaic greek's jod consonant. Although it disappeared in ancient greek, it sometimes originated a ι and may cause some vowels' contraction phenomena.",
        "w": "this is the archaic greek's digamma consonant. Although it disappeared in ancient greek, we indicate its past presence with f. ITS DISAPPERANCE LIKELY PROVOKES VOWELS' CONTRACTION PHENOMENA! BE VERY CAREFUL WITH IT!",
        "y": "usually appears in syllabograms of length 3 like ryo, tya etc. It corresponds the first consonant follows the above mentioned rules, while y may correspond to a ι, or ει.",
    }
    for i, cons in enumerate(lin_b_cons):
        mapping_entry = ET.SubElement(mapping, f"mapping_entry_{i}")
        ET.SubElement(mapping_entry, f"lb_consonant").text = cons
        for j, corr in enumerate(correspondances[cons]):
            ET.SubElement(mapping_entry, f"greek_correspondances_{j}").text = corr
        if cons in notes:
            ET.SubElement(mapping_entry, "notes").text = notes[cons]


    examples = ET.SubElement(prompt, "examples")
    ex1 = ET.SubElement(examples, "example")
    ET.SubElement(ex1, "input").text = "a-e-ti-to"
    ET.SubElement(ex1, "output").text = "αεθιστος, εθιζω"
    ex2 = ET.SubElement(examples, "example")
    ET.SubElement(ex2, "input").text = "a-di-nwa-ta"
    ET.SubElement(ex2, "output").text = "αδινfατας"
    ex3 = ET.SubElement(examples, "example")
    ET.SubElement(ex3, "input").text = "e-ma-ha"
    ET.SubElement(ex3, "output").text = "ερμαhαι, ερμαhας, ερμης"

    cot = ET.SubElement(prompt, "chain_of_thought_steps")
    ET.SubElement(cot, "step0").text = "gather as much information you can about Linear B translation into ancient greek. Get information about prefixes, suffixes, roots. Search on the internet the information you are missing to complete the task."
    ET.SubElement(cot, "step1").text = "transliterate the linear b sequence into several possible greek correspondances, accounting also for possible multiple correspondances of certain linear b consonants/vowels and contraction phenomena"
    ET.SubElement(cot, "step2").text = "if the name is not a proper name, toponym, antroponym, or patronymic, do not bilndly follow the rules, but try creative mappings with similar ancient greek words with metrics like the edit distance. Privilege more ancient documents, as Linear B is old"
    ET.SubElement(cot, "step3").text = "evaluate each proposed mapping. If it is unlikely following Chadwick rules of ancient greek written with linear b syllabograms, remove it."
    ET.SubElement(cot, "step4").text = "if the word is NOT valid, LEAVE ONLY THE MOST PROBABLE MATCHING."

    word_elem = ET.SubElement(prompt, "word")
    # anthro|ethno|phyto|topo|patro|theo   
    ET.SubElement(word_elem, "linear_b_word").text = word
    ET.SubElement(word_elem, "valid").text = str(info_dict["valid"])
    if "definition" in info_dict:
        ET.SubElement(word_elem, "definition").text = info_dict["definition"]
    if len(info_dict["cognates"]) > 0:
        cognates = ET.SubElement(word_elem, "proposed_cognates")
        for cog, val in info_dict["cognates"]:
            ET.SubElement(cognates, "ancient_greek_word").text = cog
            ET.SubElement(cognates, "matching_level").text = f"{val:.3f}"
    
    prompt = ET.tostring(prompt, "utf-8").decode()

    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel('models/gemini-2.0-flash')
    response = gemini_model.generate_content(prompt)
    pred = response.text.strip()
    return list(set(pred.split(", ")))

def make_prompt(word, info_dict, api_key):
    # Create the root XML element
    prompt = ET.Element("root")
    
    # Historical context
    context = ET.SubElement(prompt, "historical_context")
    context.text = """Linear B is a syllabic script used for writing Mycenaean Greek (1450-1200 BCE). 
    It predates alphabetic Greek by several centuries and represents an earlier stage of the language.
    The script has inherent limitations - it cannot represent consonant clusters, final consonants, or distinguish between certain phonemes 
    that were later differentiated in alphabetic Greek (like l/r or p/ph)."""
    
    # Task instructions
    instr = ET.SubElement(prompt, "task_instructions")
    ET.SubElement(instr, "task_description").text = """We are developing a model to match Linear B words with their Ancient Greek cognates.
    Your task is to analyze the Linear B word provided and suggest the most plausible Ancient Greek equivalents,
    considering phonological changes, writing conventions, and linguistic evolution. Do not explain your choices"""

    # Core rules
    rules = [
        "CRUCIAL: Use ONLY these characters in your output: fhαβγδεζηθικλμνξοπρςστυφχψω. DO NOT USE ACCENTS, SUBSCRIPT IOTA, SPIRITS.",
        "CRUCIAL: Do not blindly follow my cognates proposals, but try to reconstruct the cognates yourself. My cognates can be wrong!"
        "For syllabograms with 'ha', insert 'h' in the corresponding position in the Ancient Greek sequence",
        "For syllabograms containing 'digamma' (w), insert 'f' in the corresponding position to represent the lost sound",
        "For non-proper names, match to existing Ancient Greek lexemes with comparable grammatical function",
        "For proper names (anthroponyms, toponyms, patronymics), reconstruct through transliteration following sound change rules",
        "Output multiple cognates separated by commas only if 'valid' is True, otherwise output just one best match",
        "Consider phonological processes: assimilation, dissimilation, vowel contraction, and metathesis",
        "Pay special attention to liquid metathesis (-or-/-ro-) and consonant cluster simplification common in Mycenaean Greek"
    ]
    
    for i, r in enumerate(rules):
        ET.SubElement(instr, f"rule_{i}").text = rules[i]

    # Phonological mapping table
    mapping = ET.SubElement(prompt, "phonological_mapping")
    lin_b_cons = list("kpqrstdmnzjwhy") + ["ph"]
    correspondances = {
        "k": ["κ", "χ", "γ", "ξ"],
        "p": ["π", "φ", "ψ"],
        "q": ["β", "π", "κ", "γ", "ψ", "ξ"],
        "r": ["ρ", "λ"],
        "d": ["δ"],
        "t": ["τ", "θ"],
        "m": ["μ"],
        "n": ["ν"],
        "z": ["ζ"],
        "j": ["ι"],
        "w": ["f"],
        "h": ["h"],
        "ph": ["φ"],
        "y": ["ι", "ει"],
        "s": ["σ", "ς"]
    }
    
    # Enhanced phonological notes with more scholarly detail
    notes = {
        "k": "Linear B does not distinguish between κ, χ, and γ; these distinctions emerged later. When followed by a syllabogram with 's', it may represent ξ (ks).",
        "p": "Represents π and φ undifferentiated. May represent ψ (ps) when followed by syllabogram with 's'.",
        "q": "Typically represents labiovelar consonants that evolved into β, π, κ, or γ in Alphabetic Greek, depending on the following vowel. May represent complex consonants when followed by 's'.",
        "r": "Represents both liquids ρ and λ. Note: Chadwick's Rule - liquid consonants are often omitted in medial clusters and word-final positions in Linear B.",
        "j": "Represents yod (semivowel), which often disappears or contracts with adjacent vowels in later Greek. May produce ι or influence adjacent vowels.",
        "w": "Represents digamma (ϝ), which disappeared in Classical Greek but caused compensatory lengthening or contraction of surrounding vowels. Mark with 'f' in reconstruction.",
        "y": "In complex syllabograms (e.g., ryo, tya), typically palatalized the preceding consonant and produced ι or ει diphthong.",
        "s": "Word-final 'ς' versus word-internal 'σ' distinction emerged in Alphabetic Greek; Linear B does not make this distinction. Often the s at the beginning of a greek word does not appear in Linear B!"
    }
    
    for i, cons in enumerate(lin_b_cons):
        mapping_entry = ET.SubElement(mapping, f"mapping_entry_{i}")
        ET.SubElement(mapping_entry, f"lb_consonant").text = cons
        for j, corr in enumerate(correspondances[cons]):
            ET.SubElement(mapping_entry, f"greek_correspondance_{j}").text = corr
        if cons in notes:
            ET.SubElement(mapping_entry, "notes").text = notes[cons]

    # Add crucial vowel transformations
    vowel_info = ET.SubElement(prompt, "vowel_transformations")
    vowel_notes = {
        "a": "Generally stable as α, but may contract with adjacent vowels",
        "e": "Typically corresponds to ε, but may also represent η in certain positions",
        "i": "Corresponds to ι, may combine with following vowels to form diphthongs",
        "o": "Usually represents ο, but may also represent ω in certain positions",
        "u": "Corresponds to υ."
    }
    
    for vowel, note in vowel_notes.items():
        vowel_entry = ET.SubElement(vowel_info, f"vowel_{vowel}")
        vowel_entry.text = note

    # Common morphological patterns
    morphology = ET.SubElement(prompt, "common_morphological_patterns")
    patterns = {
        "noun_endings": "Common nominative endings: -o (masc.) → -ος, -a (fem.) → -α/-η, neuter -o → -ον",
        "case_markers": "Genitive often marked with -o-jo → -οιο → -ου (Attic-Ionic), -a-o → -αο → -ω (Doric)",
        "verbal_forms": "Present participles: -o-sa → -ουσα (fem.), -o → -ων (masc.)"
    }
    
    for key, pattern in patterns.items():
        pattern_entry = ET.SubElement(morphology, key)
        pattern_entry.text = pattern

    # Improved examples with clearer explanations
    examples = ET.SubElement(prompt, "examples")
    
    ex1 = ET.SubElement(examples, "example")
    ET.SubElement(ex1, "input").text = "a-e-ti-to"
    ET.SubElement(ex1, "output").text = "αεθιστος, εθιζω"
    ET.SubElement(ex1, "explanation").text = "The initial 'a-' could represent an augment or alpha privative. 't' corresponds to θ in this context."
    
    ex2 = ET.SubElement(examples, "example")
    ET.SubElement(ex2, "input").text = "a-di-nwa-ta"
    ET.SubElement(ex2, "output").text = "αδινfατας"
    ET.SubElement(ex2, "explanation").text = "Note the preservation of digamma (w → f) in the reconstruction, showing a sound that later disappeared."
    
    ex3 = ET.SubElement(examples, "example")
    ET.SubElement(ex3, "input").text = "e-ma-ha"
    ET.SubElement(ex3, "output").text = "ερμαhαι, ερμαhας, ερμης"
    ET.SubElement(ex3, "explanation").text = "Shows how aspiration (h) is preserved in reconstruction despite disappearing in later Greek. Also demonstrates 'r' can be inserted based on linguistic context."
    
    ex4 = ET.SubElement(examples, "example")
    ET.SubElement(ex4, "input").text = "ko-no-so" 
    ET.SubElement(ex4, "output").text = "κνωσος"
    ET.SubElement(ex4, "explanation").text = "Demonstrates vowel transformations and sound changes in a toponym (Knossos)."

    ex5 = ET.SubElement(examples, "example")
    ET.SubElement(ex5, "input").text = "a-ke-ro" 
    ET.SubElement(ex5, "output").text = "αγγελος, αχερων"
    ET.SubElement(ex5, "explanation").text = "Demonstrates that one of the cognates is more similar and easier to find, the other one (αγγελος) requires knowledge and application of ancient greek phonetic rules"

    # Refined chain of thought steps
    # Chain of thought steps with improved validation
    cot = ET.SubElement(prompt, "chain_of_thought_steps")
    
    ET.SubElement(cot, "step1").text = "Analyze the Linear B syllabograms and identify potential phoneme values for each. Create a mapping table showing all possible correspondences for each syllabogram, marking those with multiple possible interpretations."
    
    ET.SubElement(cot, "step2").text = "Validate syllabogram sequence integrity by checking for expected syllabic patterns and identifying any unusual combinations that might indicate compound words or scribal errors."
    
    ET.SubElement(cot, "step3").text = "Consider morphological patterns to identify word class (noun, verb, proper name) and potential grammatical elements (case endings, verb endings). Check if the identified morphemes align with known Mycenaean patterns."
    
    ET.SubElement(cot, "step4").text = """Apply known sound change rules between Mycenaean and Alphabetic Greek with explicit justification for each:
    - Labiovelars (qw → π/β/κ/γ depending on following vowel)
    - Liquid metathesis (or → ro in certain positions)
    - Consonant cluster simplifications
    - Compensatory lengthening after loss of semivowels
    - Assimilation at morpheme boundaries"""
    
    ET.SubElement(cot, "step5").text = """Perform consonant correspondence validation:
    - Ensure every consonant in the Linear B word has a justified match in the Greek reconstruction
    - Verify that each consonant transformation follows an attested pattern
    - Check for any unexplained deletions or insertions that might indicate errors"""
    
    ET.SubElement(cot, "step6").text = "For common words, evaluate similarity to attested Ancient Greek lexemes with comparable meaning/function. Calculate an approximate Levenshtein distance after accounting for expected phonological changes."
    
    ET.SubElement(cot, "step7").text = "For proper names, apply systematic phonological transformation while preserving recognizable elements. Check if the resulting form matches any known naming patterns or elements (-ανδρος, -κλης etc.)."
    
    ET.SubElement(cot, "step8").text = """Perform final linguistic plausibility check:
    - Verify syllable structure follows Ancient Greek phonotactics
    - Ensure accent placement is possible in the reconstructed form
    - Confirm morphological coherence (endings match gender/case)
    - Validate that each phonological transformation is linguistically motivated"""
    
    ET.SubElement(cot, "step9").text = """Rank candidates by linguistic plausibility using weighted criteria:
    - Phonological regularity (40%)
    - Morphological coherence (10%)
    - Semantic appropriateness (20%)
    - Attestation in Ancient Greek corpus (30%)
    If 'valid' is False, propose only the single most likely match. If 'valid' is True, output at most 5 highest-ranked cognates, separated by commas."""
    
    # Add validation mechanisms section
    validation = ET.SubElement(prompt, "validation_mechanisms")
    
    phonological_validation = ET.SubElement(validation, "phonological_validation")
    phonological_validation.text = """For each proposed cognate, create a syllable-by-syllable mapping showing:
    1. The original Linear B syllabogram
    2. The corresponding Greek phonemes
    3. The specific rule/transformation applied
    4. Justification for any phoneme that doesn't follow the standard correspondence
    Reject any mapping where a consonant lacks clear justification or where multiple unusual transformations occur without linguistic motivation."""
    
    morphological_validation = ET.SubElement(validation, "morphological_validation")
    morphological_validation.text = """Verify that:
    1. The word ending matches expected grammatical features
    2. The stem follows expected phonological patterns
    3. For verbs: tense/mood/voice markers are consistent
    4. For nouns: case/number/gender markers are consistent
    5. Any prefixes or compound elements follow attested patterns in Mycenaean or early Greek"""
    
    semantic_validation = ET.SubElement(validation, "semantic_validation")
    semantic_validation.text = """If definition or context is provided:
    1. Ensure the cognate's meaning aligns with provided definition
    2. Check that the word class is appropriate for context
    3. For toponyms/anthroponyms: verify the reconstruction preserves core phonological elements
    4. Reject semantically implausible matches even if phonologically regular"""
    
    # Add error checking section
    error_checks = ET.SubElement(prompt, "error_checking")
    
    common_errors = ET.SubElement(error_checks, "common_errors")
    common_errors.text = """Watch for these common reconstruction errors:
    1. Incorrect handling of liquid metathesis (or/ro alternations)
    2. Failure to account for labiovelar transformations
    3. Inappropriate vowel length in compensatory lengthening contexts
    4. Missing digamma effects on surrounding vowels
    5. Implausible consonant clusters for Greek phonotactics
    6. Misapplication of synchronic vs. diachronic phonological rules"""
    
    consistency_check = ET.SubElement(error_checks, "consistency_check")
    consistency_check.text = """After generating candidates:
    1. Double-check that all syllabograms are accounted for
    2. Verify phonological rules are applied consistently throughout the word
    3. Confirm that any unusual correspondences are justified by analogous attested examples
    4. Ensure the phonological trajectory from Mycenaean to Alphabetic Greek is chronologically plausible"""

    # Word information section
    word_elem = ET.SubElement(prompt, "word")
    ET.SubElement(word_elem, "linear_b_word").text = word
    ET.SubElement(word_elem, "valid").text = str(info_dict["valid"])
    
    if "definition" in info_dict:
        ET.SubElement(word_elem, "definition").text = info_dict["definition"]
    
    if len(info_dict["cognates"]) > 0:
        cognates = ET.SubElement(word_elem, "proposed_cognates")
        for cog, val in info_dict["cognates"]:
            ET.SubElement(cognates, "ancient_greek_word").text = cog
            ET.SubElement(cognates, "matching_level").text = f"{val:.3f}"
    
    # Special handling for named entities
    if "type" in info_dict:
        ET.SubElement(word_elem, "entity_type").text = info_dict["type"]
        
        if info_dict["type"] == "anthroponym":
            ET.SubElement(word_elem, "naming_pattern_note").text = "Personal names often preserve older phonological features and may contain recognizable elements like -λαος, -κλης, -ανδρος"
        elif info_dict["type"] == "toponym":
            ET.SubElement(word_elem, "naming_pattern_note").text = "Place names frequently preserve pre-Greek elements and may not follow standard Greek phonological patterns"
    
    prompt = ET.tostring(prompt, "utf-8").decode()

    # Using Gemini model to generate response
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel('models/gemini-2.0-flash')
    response = gemini_model.generate_content(prompt)
    pred = response.text.strip()
    return list(set(pred.split(", ")))

# Open the file in write mode ('w') first, to clear it before writing new data
out = "cognates.cog"
with open(out, "w", encoding="utf-8") as f:
    # Write the header to the file (this happens only once at the beginning)
    f.write("converted_linear_b\tgreek\tgemini\tvalid\n")
    f.flush()
    # Initialize previous index to check for the change in api_key usage
    prec_idx = 0
    
    # Iterate through the matching keys
    for i, word in tqdm(enumerate(matching.keys())):
        # Sleep logic for API call limit
        #if i != 0 and i % (15 * len(api_keys)) == 0:
        #    time.sleep(25)
        
        # Determine which API key to use
        idx = (i % (15 * len(api_keys))) // 15
        api_key = api_keys[idx]
        print(api_key)
        
        # Check if the API key has changed and sleep for a while if it has
        if idx != prec_idx:
            time.sleep(3)
        prec_idx = idx
        
        # Make the request and get the response
        matching[word]["gemini"] = make_prompt(word, matching[word], api_key)
        
        # Now, append each line to the file right after processing the response
        max_likelihood = 0
        to_insert = []
        for cog in matching[word]["cognates"]:
            max_likelihood = max(max_likelihood, cog[1])
            if cog[1] == max_likelihood:
                to_insert.append(cog[0])
        
        # Collect Gemini responses
        gemini = [cog for cog in matching[word]["gemini"]]
        
        # Join the lists with a pipe separator
        to_insert = "|".join(to_insert)
        gemini = "|".join(gemini)
        
        # Append the results for the current word to the file
        with open(out, "a", encoding="utf-8") as f_append:
            f_append.write(f"{word}\t{to_insert}\t{gemini}\t{int(matching[word]['valid'])}\n")
