from collections import defaultdict
import re



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
            if i < 560: continue
            if i > 565: break
            
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
    for lb in lin_b_words.keys():
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
            if not(lb == "a-da-wa-si-jo" and g == "a*odras"): continue
            while i < len(lb_list) and j < len(g_list):
                print(i, j, lb_list[i:], g_list[j:], skipped, skipped_consecutive, max_sc)
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
                        if (g_char == "p" or g_char == "*") and g_list[j+1] == lb_syl[1] and g_list[j+2] == lb_syl[2]:
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

out = "cognates.cog"
with open(out, "w", encoding="utf-8") as f:
    f.write("converted_linear_b\tgreek\tvalid\n")
    for k in matching.keys():
        max_likelihood = 0
        to_insert = []
        for cog in matching[k]["cognates"]:
            max_likelihood = max(max_likelihood, cog[1])
            if cog[1] == max_likelihood:
                to_insert.append(cog[0])
        to_insert = "|".join(to_insert)
        f.write(f"{k}\t{to_insert}\t{int(matching[k]['valid'])}\n")


