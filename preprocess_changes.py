'''
# Define input and output file paths
input_file = 'changes.txt'
output_file = 'outputone.txt'

# Read the input file
with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Split the content on commas
values = content.split(',')

# Write each value on a new line to the output file
with open(output_file, 'w', encoding='utf-8') as f:
    for value in values:
        f.write(value.strip() + '\n')

print("File has been processed and rewritten.")
'''
'''
import unicodedata

# Input and output file paths
input_file = 'outputone.txt'
output_file = 'output.txt'

def contains_greek(text):
    return any('\u0370' <= char <= '\u03FF' for char in text)

def normalize_greek(word):
    decomposed = unicodedata.normalize('NFD', word)
    base_only = ''.join(char for char in decomposed if unicodedata.category(char) != 'Mn')
    return base_only.lower()

with open(input_file, 'r', encoding='utf-8') as fin, open(output_file, 'w', encoding='utf-8') as fout:
    for line in fin:
        parts = line.strip().split(' ')
        if parts and contains_greek(parts[0]):
            parts[0] = normalize_greek(parts[0])
            fout.write(' '.join(parts) + '\n')
        else:
            fout.write(line)

print("Conditional Greek normalization complete.")
'''
import csv
# put in a list each line of the cognates file
def parse_tsv(file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        data = [row for row in reader]
    return [{}, {}] + data

# Example usage:
rows = parse_tsv('cognates.cog')

def write_tsv(file_path, rows):
    if not rows or not isinstance(rows, list):
        raise ValueError("Empty or invalid data provided.")

    # The first row should be a dictionary; use its keys as headers
    headers = rows[0].keys()

    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers, delimiter='\t')
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

filename = 'output.txt'
# open changes file
with open(filename, 'r', encoding='utf-8') as f:
    lines = f.readlines()
lines = [l.strip() for l in lines]

for correction in lines[::-1]:
    correction = correction.split(" ")
    if len(correction) == 1:
        index = int(correction[0])
        dictionary = rows[index]
        likelihood_string = dictionary['likelihood']
        vals = likelihood_string.split("|")
        vals = ['0.6'] * len(vals)
        dictionary['likelihood'] = "|".join(vals)
        rows[index] = dictionary

    elif correction[1] == "good":
        index = int(correction[0])
        dictionary = rows[index]
        likelihood_string = dictionary['likelihood']
        vals = likelihood_string.split("|")
        vals[0] = '0.8'
        dictionary['likelihood'] = "|".join(vals)
        rows[index] = dictionary
    else:
        greek_words = correction[0]
        index = int(correction[1])
        dictionary = rows[index]
        dictionary['gemini'] = greek_words
        dictionary['likelihood'] = ("0.8|" * (greek_words.count("|") + 1))[:-1]
        rows[index] = dictionary
        #print(greek_words, dictionary)
        
write_tsv("corrected_cognates.cog", rows[2:])
