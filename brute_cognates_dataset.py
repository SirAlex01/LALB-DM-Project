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
#api_keys = [os.getenv("GOOGLE_API_KEY_10"), os.getenv("GOOGLE_API_KEY_11"), os.getenv("GOOGLE_API_KEY_12"), os.getenv("GOOGLE_API_KEY_13")]



def latinize_greek(greek_file, latinized_greek_file):
    # Greek-to-Latin character mapping dictionary
    greek_to_latin = {
        'α': 'a', 'β': 'q', 'γ': 'k', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'e', 'θ': 't',
        'ι': 'i', 'κ': 'k', 'λ': 'r', 'μ': 'm', 'ν': 'n', 'ξ': 'ks', 'ο': 'o', 'π': '#',
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
        for i, r in enumerate(f):
            # DEBUG
            #if i < 620: continue
            #if i > 200: break
            
            word, valid, _ = r.strip().split("\t")
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
                        if g_char == "p" or g_char == "#":
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
                        if g_char == "q" or g_char == "#" or g_char == "k":
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
                    if old_i != len(lb_list)-1 and (lb_list[old_i][0] == g_list[old_j] or (lb_list[old_i][0] == "p" and g_list[old_j] == "#")):
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
                        if j+2 < len(g_list) and (g_char == "p" or g_char == "#") and g_list[j+1] == lb_syl[1] and g_list[j+2] == lb_syl[2]:
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
                        #print(lb_syl, g_char)
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
            begin_with_same = lb[0] == g[0] or (lb[0] == "p" and g_list[0] == "#") or (lb[0] == "t" and g_list[0] == "s" and g_list[1] == "t") or \
                              (lb[0] == "w" and g_list[0] == "f") or  (lb[0] == "q" and (g_list[0] == "k" or g_list[0] == "#")) or \
                              (lb[0] == "p" and g_list[0] == "s" and g_list[1] == "p") or lb[0] == "*"
            
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
# File where the matching dictionary is saved
matching_file = "matching.pkl"
MAX_LEN = 10
if not os.path.exists(matching_file):
    # Collect words and compute matching
    lin_b_words = collect_lin_b_words("linb_words.tsv")
    greek_words = collect_greek_words("latinized_homeric_greek_words.tsv")
    
    matching = match(lin_b_words, greek_words)
    #matching = match({"*18-jo":{"cognates":[], "valid":True}}, {"toio":""})

    # Sort cognates by likelihood score
    for k in matching.keys():
        if len(matching[k]["cognates"]) > MAX_LEN:
            matching[k]["cognates"] = random.sample(matching[k]["cognates"], MAX_LEN)
        matching[k]["cognates"] = sorted(matching[k]["cognates"], key=lambda x: x[1], reverse=True)

    # Save to file
    with open(matching_file, "wb") as f:
        pickle.dump(matching, f)
    print("Created and saved matching.")
else:
    # Load from file
    with open(matching_file, "rb") as f:
        matching = pickle.load(f)
    print("Loaded matching from file.")

for k in matching.keys():
    matching[k]["type"] = "common"

proper_names_types = ["anthroponym", "ethnonym", "phytonym", "toponym", "patronymic", "theonym"]
# Open and process the CSV file
with open("Linear B Lexicon.csv", newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    
    for row in reader:
        transcription = row["transcription"]
        transcription = transcription.replace("pu2","phu").replace("ro2","ryo").replace("ra2", "rya").replace("ra3", "rai").replace("ta2", "tya").replace("a2","ha").replace("a3","ai")

        #assert transcription in matching.keys()
        if transcription in matching:
            matching[transcription]["definition"] = row["definition"]
            for pn in proper_names_types:
                if pn in row["definition"]:
                    matching[transcription]["type"] = "proper"
                    break

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
    
    # Historical context and linguistic principles
    principles = ET.SubElement(prompt, "linguistic_principles")
    principles.text = """Linear B is a syllabic script used for writing Mycenaean Greek (1450-1200 BCE).
    When matching Linear B words with their Greek cognates, the following fundamental principles of historical linguistics must be observed:"""
    
    # The four key principles from the paper
    key_principles = [
        "1. Distributional Similarity of Matching Characters: Corresponding characters tend to appear in similar contexts in both languages. Their phonetic environments should show consistent correspondence patterns.",
        "2. Monotonic Character Mapping within Cognates: Matching cognates rarely exhibit character reordering. The alignment between Linear B and ancient Greek must preserve the relative ordering of phonemes, with transformations following systematic phonetic rules.",
        "3. Structural Sparsity of Cognate Mapping: As documented in historical linguistics, cognate matches are mostly one-to-one, since both words are derived from the same proto-origin. Avoid unjustified many-to-many correspondences.",
        "4. Significant Cognate Overlap Within Related Languages: The derived vocabulary mapping should have sufficient coverage for lost language cognates (Linear B). Prioritize correspondences that reinforce systematic patterns already observed."
    ]
    
    for i, principle in enumerate(key_principles):
        ET.SubElement(principles, f"principle_{i+1}").text = principle
    
    # Task instructions
    instr = ET.SubElement(prompt, "task_instructions")
    ET.SubElement(instr, "task_description").text = """Analyze the provided Linear B word and propose the most plausible Ancient Greek cognates,
    rigorously applying the four principles of historical linguistics listed above.
    Limit your response to a maximum of 3 cognates, selecting only those with the highest linguistic probability."""

    # Core rules
    rules = [
    	"OUTPUT: Maximum 3 cognates separated by commas if 'valid' is True, otherwise only the best match",
        "CRUCIAL: Use ONLY these characters in your output: fhαβγδεζηθικλμνξοπρςστυφχψω. do NOT use ANY OTHER LATIN CHARACTER, ACCENTS, SUBSCRIPT IOTA, SPIRITS.",
        "CRUCIAL: Consider that our proposed cognates are just proposals of words with similar root in the Homeric scripts. DO NOT RELY ON THEM FOR FINDING THE COGNATES, FIND THEM YOURSELF FROM THE ENTIRE ANCIENT GREEK CORPUS!!!"
        "For each proposed correspondence, verify that it is consistent with Principle 1 (Distributional Similarity)",
        "Every transformation must respect the relative ordering of phonemes, as required by Principle 2 (Monotonic Mapping)",
        "Prioritize one-to-one correspondences between phonemes, as indicated by Principle 3 (Structural Sparsity)",
        "Verify that your proposals align with correspondence patterns already documented between Linear B and ancient Greek (Principle 4)",
        "For syllabograms with 'ha', insert 'h' in the corresponding position in the Ancient Greek sequence",
        "For syllabograms containing 'digamma' (w), insert 'f' in the corresponding position",
        "QUALITY CHECK: If you have uncertainties about a cognate, DO NOT include it in the output"
    ]
    
    for i, r in enumerate(rules):
        ET.SubElement(instr, f"rule_{i}").text = rules[i]

    # Phonological mapping table (keeping the existing part)
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
    
    notes = {
        "k": "Linear B does not distinguish between κ, χ, and γ. May become ξ, usually when followed by a syllabogram starting with s. Principle 3: maintain one-to-one correspondences where possible.",
        "p": "Represents π and φ undifferentiated. May become ψ, usually when followed by a syllabogram starting with s. Principle 1: consider phonetic context to determine the correct correspondence.",
        "q": "Typically represents labiovelar consonants. May become ξ or ψ, usually when followed by a syllabogram starting with s. Principle 2: ensure transformations follow documented sound change patterns.",
        "r": "Represents both liquids ρ and λ. Apply Principle 4 to determine the most likely correspondence in this specific context.",
        "j": "Represents yod (semivowel). Principle 1: examine distributional patterns to determine its most likely Greek reflex.",
        "w": "Represents digamma (ϝ). Principle 3: mark with 'f' to maintain structural sparsity in the mapping.",
        "y": "In complex syllabograms. Principle 2: ensure monotonic mapping when resolving to ι or ει.",
        "s": "Apply Principles 1 and 4 to determine whether word-final 'ς' or word-internal 'σ' is appropriate."
    }
    
    for i, cons in enumerate(lin_b_cons):
        mapping_entry = ET.SubElement(mapping, f"mapping_entry_{i}")
        ET.SubElement(mapping_entry, f"lb_consonant").text = cons
        for j, corr in enumerate(correspondances[cons]):
            ET.SubElement(mapping_entry, f"greek_correspondance_{j}").text = corr
        if cons in notes:
            ET.SubElement(mapping_entry, "notes").text = notes[cons]

    # Add vowel transformations with principles-based guidance
    vowel_info = ET.SubElement(prompt, "vowel_transformations")
    vowel_notes = {
        "a": "Generally stable as α. Principle 1: examine distributional context for potential contractions.",
        "e": "Typically corresponds to ε, but may represent η in certain positions. Apply Principle 4 based on documented patterns.",
        "i": "Corresponds to ι. Apply Principle 2 to maintain monotonic mapping with any adjacent vowels.",
        "o": "Usually represents ο, but may represent ω in certain positions, especially at the end of the words in verbs. Apply Principle 3 for sparsity in mapping.",
        "u": "Corresponds to υ. Apply Principles 1 and 4 to determine the most likely correspondence."
    }
    
    for vowel, note in vowel_notes.items():
        vowel_entry = ET.SubElement(vowel_info, f"vowel_{vowel}")
        vowel_entry.text = note

    # Examples with principle-based explanations
    examples = ET.SubElement(prompt, "examples")

    ex1 = ET.SubElement(examples, "example")
    ET.SubElement(ex1, "input").text = "a-e-ti-to"
    ET.SubElement(ex1, "output").text = "αεθιστος, εθιζω"
    ET.SubElement(ex1, "principles_applied").text = "Principle 1: t → θ correspondence follows consistent patterns. Principle 2: Preserves monotonic ordering of phonemes. Principle 3: Maintains one-to-one mapping between Linear B and Greek sounds."

    ex2 = ET.SubElement(examples, "example")
    ET.SubElement(ex2, "input").text = "a-di-nwa-ta"
    ET.SubElement(ex2, "output").text = "αδινfατας"
    ET.SubElement(ex2, "principles_applied").text = "Principle 2: Preserves monotonic mapping in nw → νf sequence. Principle 4: Consistent handling of digamma (w → f) reinforces observed patterns."

    ex3 = ET.SubElement(examples, "example")
    ET.SubElement(ex3, "input").text = "e-ma-ha"
    ET.SubElement(ex3, "output").text = "ερμαhαι, ερμαhας"
    ET.SubElement(ex3, "principles_applied").text = "Principle 1: Distributional similarity used to infer ρ. Principle 3: Structural sparsity maintained with one-to-one sound mapping. Principle 4: Consistent h-series representation."

    ex4 = ET.SubElement(examples, "example")
    ET.SubElement(ex4, "input").text = "ko-no-so" 
    ET.SubElement(ex4, "output").text = "κνωσος"
    ET.SubElement(ex4, "principles_applied").text = "All four principles applied: Principle 1: k/o sound correspondence. Principle 2: Monotonic ordering preserved. Principle 3: One-to-one mapping. Principle 4: Aligns with known patterns for toponyms."

    ex5 = ET.SubElement(examples, "example")
    ET.SubElement(ex5, "input").text = "wo-no-qe-wa"
    ET.SubElement(ex5, "output").text = "fονοκεfα"
    ET.SubElement(ex5, "principles_applied").text = "Principle 1: w → f and q → κ correspondences follow consistent patterns. Principle 2: Monotonic ordering preserved. Principle 4: Reinforces observed digamma patterns."

    ex6 = ET.SubElement(examples, "example")
    ET.SubElement(ex6, "input").text = "wo-ro-ki-jo-ne-jo"
    ET.SubElement(ex6, "output").text = "fοργιονειος, οργεωνες"
    ET.SubElement(ex6, "principles_applied").text = "Principle 1: Distributional similarity in vowel sequences. Principle 2: Preserves monotonic mapping. Principle 4: Aligns with suffix transformation patterns."

    ex7 = ET.SubElement(examples, "example")
    ET.SubElement(ex7, "input").text = "qi-si-pe-e"
    ET.SubElement(ex7, "output").text = "ξιφεε, ξιφη"
    ET.SubElement(ex7, "principles_applied").text = "Principle 1: q + s → ξ correspondence in this context. Principle 3: Maintains sparse one-to-one mapping. Principle 4: Vowel contraction pattern (e-e → η) follows established rules."

    ex8 = ET.SubElement(examples, "example")
    ET.SubElement(ex8, "input").text = "re-u-ko-to-ro"
    ET.SubElement(ex8, "output").text = "λευκτρον, λευκτροι"
    ET.SubElement(ex8, "principles_applied").text = "Principle 1: r → λ distributional context. Principle 2: Preserves monotonic mapping. Principle 3: Maintains sparse mapping in consonant clusters. Principle 4: Aligns with known toponym patterns."

    ex9 = ET.SubElement(examples, "example")
    ET.SubElement(ex9, "input").text = "qo-u-qo-ta"
    ET.SubElement(ex9, "output").text = "βουβοτας"
    ET.SubElement(ex9, "principles_applied").text = "Principle 1: q → β correspondence in appropriate contexts. Principle 2: Preserves monotonic mapping. Principle 4: Diphthong formation patterns (o-u → ου) align with documented cases."

    ex10 = ET.SubElement(examples, "example")
    ET.SubElement(ex10, "input").text = "qe-qi-no-me-na"
    ET.SubElement(ex10, "output").text = "γεγινωμενα"
    ET.SubElement(ex10, "principles_applied").text = "Principle 1: q → γ correspondence in specific environments. Principle 2: Monotonic mapping preserved. Principle 4: Verbal form transformations follow established patterns."

    ex11 = ET.SubElement(examples, "example")
    ET.SubElement(ex11, "input").text = "po-ro-wi-to-jo"
    ET.SubElement(ex11, "output").text = "πλωfιστοιο"
    ET.SubElement(ex11, "principles_applied").text = "Principle 2: Monotonic mapping preserved despite syllable reduction. Principle 3: Maintains structural sparsity. Principle 4: Genitive ending transformation follows documented patterns."

    ex12 = ET.SubElement(examples, "example")
    ET.SubElement(ex12, "input").text = "po-ti-pi"
    ET.SubElement(ex12, "output").text = "πορτις, πορτιφι"
    ET.SubElement(ex12, "principles_applied").text = "Principle 1: Context-appropriate sound correspondences. Principle 3: One-to-one mapping maintained. Principle 4: Case ending transformation follows established patterns."

    ex13 = ET.SubElement(examples, "example")
    ET.SubElement(ex13, "input").text = "a-ri-qa"
    ET.SubElement(ex13, "output").text = "αρισβας"
    ET.SubElement(ex13, "principles_applied").text = "Principle 1: q → β correspondence in this phonetic environment. Principle 2: Monotonic mapping preserved. Principle 4: Consonant addition follows patterns observed in anthroponyms."

    ex14 = ET.SubElement(examples, "example")
    ET.SubElement(ex14, "input").text = "ko-no"
    ET.SubElement(ex14, "output").text = "σκοινος"
    ET.SubElement(ex14, "principles_applied").text = "Principle 1: Initial k- often corresponds to σκ- in Greek. Principle 2: Monotonic mapping preserved with initial consonant addition. Principle 4: Aligns with observed prosthetic consonant patterns."
    # Refined evaluation criteria based on the principles
    evaluation = ET.SubElement(prompt, "evaluation_criteria")
    
    ET.SubElement(evaluation, "criterion_1").text = """Distributional Similarity Score (Principle 1):
    - High: Each character appears in similar phonetic environments in both words
    - Medium: Most characters show distributional similarity
    - Low: Significant distributional mismatches
    Only propose cognates with High or Medium scores."""
    
    ET.SubElement(evaluation, "criterion_2").text = """Monotonicity Assessment (Principle 2):
    - Verify that the relative ordering of phonemes is preserved
    - Check that any insertions/deletions follow documented phonological rules
    - Reject any mapping that requires unjustified reordering of characters"""
    
    ET.SubElement(evaluation, "criterion_3").text = """Structural Sparsity Check (Principle 3):
    - Count the number of one-to-many or many-to-one mappings
    - Verify each non-one-to-one mapping has strong linguistic justification
    - Prefer cognates with higher percentage of one-to-one mappings"""
    
    ET.SubElement(evaluation, "criterion_4").text = """Coverage Assessment (Principle 4):
    - Check how well the proposed mapping aligns with documented patterns
    - Verify that any novel correspondences have strong linguistic justification
    - Prioritize cognates that reinforce established correspondence patterns"""

    # Chain of thought steps aligned with principles
    cot = ET.SubElement(prompt, "chain_of_thought_steps")
    
    ET.SubElement(cot, "step1").text = """Analyze the Linear B syllabograms and identify potential phoneme values.
    Create a mapping table showing possible correspondences, evaluating each against Principle 1 (Distributional Similarity)."""
    
    ET.SubElement(cot, "step2").text = """Apply Principle 2 (Monotonic Mapping) to:
    - Preserve the relative order of phonemes
    - Account for documented sound changes
    - Reject mappings requiring unjustified reordering"""
    
    ET.SubElement(cot, "step3").text = """Apply Principle 3 (Structural Sparsity) to:
    - Prioritize one-to-one phoneme correspondences
    - Justify any one-to-many or many-to-one mappings
    - Quantify the sparsity of each proposed mapping"""
    
    ET.SubElement(cot, "step4").text = """Apply Principle 4 (Cognate Overlap) to:
    - Check alignment with documented Linear B to Greek correspondence patterns
    - Evaluate how the proposed cognate reinforces or extends known patterns
    - Calculate a coverage score based on pattern alignment"""
    
    ET.SubElement(cot, "step5").text = """Rank candidate cognates by composite score across all four principles:
    - Distributional Similarity Score (25%)
    - Monotonicity Score (25%)
    - Structural Sparsity Score (25%)
    - Pattern Coverage Score (25%)
    If 'valid' is False, propose only the single highest-ranked cognate. 
    If 'valid' is True, output at most 3 highest-ranked cognates, separated by commas."""
    
    # Final quality control filter
    quality_filter = ET.SubElement(prompt, "quality_control")
    quality_filter.text = """Final Quality Control:
    1. For each proposed cognate, explicitly verify all four principles
    2. Reject any cognate with a low score on any principle
    3. Limit output to maximum 3 highest-quality cognates (if valid=True)
    4. Output only a single highest-quality cognate (if valid=False)
    5. If uncertain about quality, prefer to output fewer cognates"""
    
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
    
    ET.SubElement(word_elem, "entity_type").text = info_dict["type"] + " name"
        

    # Create output format section with rules
    output_format = ET.SubElement(prompt, "output_format")
    ET.SubElement(output_format, "output_description").text = """format your output in json.
    Return an array of cognates (even if you are returning a single one) containing three fields: 
    - the field cognate containing the cognate itself;
    - the field likelihood containing an estimate between 0 and 1 of how much you are sure the words are cognates
    - the field note containing the reasoning behind the choice, the applied phenomena and the passed and unpassed checks.
    For the cognate field, STRICTLY FOLLOW THE OUTPUT FORMATTING RULES"""
    
    output_rules = [
        "CHARACTER SET: use ONLY these characters: fhαβγδεζηθικλμνξοπρςστυφχψω. DO NOT use accents, breathing marks, subscript iota, or other diacritics."
        "FORMAT: if valid=True: Output up to 3 cognates. If valid=False: Output only the single best match."
    ]

    
    for i, r in enumerate(output_rules):
        ET.SubElement(output_format, f"output_formatting_rule_{i}").text = output_rules[i]

    likelihood_calibration = ET.SubElement(output_format, "likelihood_calibration")
    ET.SubElement(likelihood_calibration, "calibration_instructions").text = """When estimating likelihood, use the following calibrated scale:
    0.95-1.00: Reserved ONLY for established cognates confirmed in scholarly literature with near certainty
    0.75-0.94: Strong evidence with multiple corresponding patterns and minimal uncertainties
    0.50-0.74: Good evidence but with some uncertainties or competing explanations
    0.40-0.49: Plausible connection with significant uncertainties
    0.20-0.39: Speculative connection with major uncertainties
    0.00-0.19: Highly speculative with minimal supporting evidence"""

    downweighting = ET.SubElement(likelihood_calibration, "automatic_downweighting")
    ET.SubElement(downweighting, "factor_1").text = """Reduce likelihood by 0.2-0.3 if the cognate requires:
    - Three or more non-trivial sound transformations
    - Any reordering of phonemes
    - Addition/deletion of multiple phonemes."""

    ET.SubElement(downweighting, "factor_2").text = """Reduce likelihood by 0.1-0.2 if:
    - The word is rare in the corpus
    - The cognate proposal conflicts with existing scholarship
    - The semantic match requires significant stretching."""

    ET.SubElement(downweighting, "factor_3").text = """Reduce likelihood by 0.35-0.4 if an unknown syllabogram appears in the linear B sequence. The likelihood of sequences with unknown syllabograms MUST ALWAYS BE LESS THAN 0.7 ."""

    ET.SubElement(downweighting, "factor_4").text = """Even if all principles are satisfied, without attestation in scholarly literature, 
    no novel cognate proposal should receive likelihood above 0.85."""

    calibration_examples = ET.SubElement(likelihood_calibration, "example_likelihoods")
    ET.SubElement(calibration_examples, "high_example").text = """ko-no-so → κνωσος: likelihood = 0.95 
    (Near certainty: well-documented toponym with scholarly consensus)"""

    ET.SubElement(calibration_examples, "medium_high_example").text = """a-ko-ra → αγορα: likelihood = 0.85 
    (Good correspondence but with some phonological uncertainties)"""

    ET.SubElement(calibration_examples, "medium_example").text = """po-ti-ni-ja → ποτνια: likelihood = 0.75 
    (Reasonable correspondence but requires several transformations)"""

    ET.SubElement(calibration_examples, "lower_medium_example").text = """a-re-ka-sa-da-ra → αλεξανδρα: likelihood = 0.65 
    (Plausible but with multiple phonological adaptations and uncertainties)"""

    ET.SubElement(calibration_examples, "lower_medium_example").text = """pe-ma → σπερμα: likelihood = 0.65 
    (Speculative connection requiring multiple unsupported transformations)"""

    ET.SubElement(calibration_examples, "low_example").text = """a-ka-ma-to → αγαμαι: likelihood = 0.5 
    (Unclear transformation at the end of the word, now matching suffixes but probably a similar root)"""
    
    ET.SubElement(calibration_examples, "lower_example").text = """*47-so-de → ασος: likelihood = 0.4
    (Unclear transformation in the suffix and unknown syllabogram in the sequence)"""

    ET.SubElement(calibration_examples, "lower_example").text = """*34-za-te-si → ζατεσις: likelihood = 0.3
    (Unknown syllabogram in the sequence, complete omission of a syllabogram for no good reason)"""

    ET.SubElement(calibration_examples, "lower_example").text = """*56-ko-qe → κλαγγη: likelihood = 0.2 
    (Plenty of unclear transformation phenomena and unknown syllabogram in the sequence)"""

    ET.SubElement(calibration_examples, "lower_example").text = """*56-ni-di-ja → ανδρα: likelihood = 0.0 
    (No clear connection or matching between the two words)"""

    critical_thinking = ET.SubElement(output_format, "critical_evaluation")
    ET.SubElement(critical_thinking, "instruction").text = """For each cognate proposal:
    - Actively search for weaknesses in the proposed cognate connection
    - List at least one specific uncertainty or alternative explanation
    - Consider what evidence would be needed to increase confidence
    - Apply higher standards for novel cognate proposals than for established ones"""

    ET.SubElement(critical_thinking, "uncertainty_prompt").text = """Before finalizing your likelihood score, ask:
    - What scholarly sources would I need to confirm this?
    - What alternative cognates might explain this Linear B term?
    - What specific sound changes require justification?
    - Would experts in Mycenaean Greek agree with this analysis?"""
    # Generate XML string
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

# Open the file in write mode ('w') first, to clear it before writing new data

out = "cognates.cog"

# Check if file exists
file_exists = os.path.exists(out)

# If file doesn't exist, create it and write the header
if not file_exists:
    with open(out, "w", encoding="utf-8") as f:
        f.write("converted_linear_b\tgreek\tgemini\tvalid\tlikelihood\tsequence_id\n")
        f.flush()
    start_index = 0
else:
    # If file exists, count the number of existing data rows (excluding header)
    with open(out, "r", encoding="utf-8") as f:
        line_count = sum(1 for line in f) - 1  # subtract 1 for header
    start_index = line_count

# Initialize previous index for API key management
prec_idx = 0

#Get sequences lists ids of words (where they appear)
seq_lists_file = "./linb_words.tsv"
words2seqlist = {}
with open(seq_lists_file, "r", encoding="utf-8") as lin_b_words_file:
    line = lin_b_words_file.readline().strip().split("\t")
    while line != [''] and line is not None:
        words2seqlist[line[0]] = line[2]
        line = lin_b_words_file.readline().strip().split("\t")
       

# Iterate through the matching keys starting from where we left off
for i, word in tqdm(enumerate(sorted(matching.keys())[start_index:], start=start_index)):
    # Determine which API key to use
    #if i % 300 == 0:
    #    time.sleep(60)
    idx = (i % (15 * len(api_keys))) // 15
    api_key = api_keys[idx]
    print(api_key, word)

    # Check if the API key has changed
    if idx != prec_idx:
        time.sleep(5)
    prec_idx = idx

    while True:
        try:
            # Attempt to make the request and get the response
            gemini_cognates = make_prompt(word, matching[word], api_key)
            matching[word]["gemini"] = gemini_cognates
            break  # Exit the loop if successful
        except Exception as e:
            print(f"Error occurred: {e}. Retrying in 65 seconds...")
            time.sleep(65)

    # Find the max likelihood cognates
    max_likelihood = 0
    to_insert = []
    for cog in matching[word]["cognates"]:
        max_likelihood = max(max_likelihood, cog[1])
        if cog[1] == max_likelihood:
            to_insert.append(cog[0])

    # Collect unique cognate surface forms (in order of appearance)
    unique_gemini = sorted(
        list(OrderedDict.fromkeys((cog['cognate'], cog['likelihood']) for cog in gemini_cognates if 'cognate' in cog and 'likelihood' in cog)),
        key=lambda x: x[1],  # Sort by the likelihood (second element in the tuple)
        reverse=True  # Set to True to sort in descending order (highest likelihood first)
    )

    to_insert = "|".join(to_insert)
    gemini_cogs = [cog[0] for cog in unique_gemini]  # Extract cognates
    gemini_likelihoods = [str(cog[1]) for cog in unique_gemini]  # Extract likelihoods and convert to strings
    # Join them with "|" separator
    gemini_cogs = "|".join(gemini_cogs)
    gemini_likelihoods = "|".join(gemini_likelihoods)

    seq_list = words2seqlist[word]
    # Append the results
    with open(out, "a", encoding="utf-8") as f_append:
        f_append.write(f"{word}\t{to_insert}\t{gemini_cogs}\t{int(matching[word]['valid'])}\t{gemini_likelihoods}\t{seq_list}\n")
    
    with open("gemini_output.jsonl", "a", encoding="utf-8") as f_jsonl:
        json_line = json.dumps({word: {"valid": matching[word]['valid'], "output": gemini_cognates}}, ensure_ascii=False)
        f_jsonl.write(json_line + "\n")

