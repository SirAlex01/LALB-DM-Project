import csv

# Load the TSV file (cognates_dataset.cog), skipping the header
cognates_dataset = {}
with open('cognates_dataset.cog', 'r', encoding='utf-8') as tsvfile:
    reader = csv.reader(tsvfile, delimiter='\t')
    next(reader)  # Skip header
    for row in reader:
        if row:  # Skip empty lines
            cognates_dataset[row[0]] = row[1].split("|")

# Load the CSV file (gemini_output.txt), skipping the header
gemini_output = []
with open('./additional_lexicon/gemini_output.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # Skip header
    for i, row in enumerate(reader):
        if row:  # Skip empty lines
            gemini_output.append({
                'linear_b': row[0],
                'greek_cognates': row[1].split("|"),
                'dubious': row[2],
                'explanation': row[3],
                'translation': row[4]
            })

for tuple in gemini_output:
    if tuple['linear_b'] not in cognates_dataset:
        cognates_dataset[tuple['linear_b']] = tuple['greek_cognates']
    else:
        for cog in tuple['greek_cognates']:
            if cog not in cognates_dataset[tuple['linear_b']]:
                cognates_dataset[tuple['linear_b']].append(cog)      

entries = [(lb, greek_list) for (lb, greek_list) in cognates_dataset.items()]
entries.sort(key = lambda x:x[0])
with open('cognates_final.cog', 'w', encoding='utf-8', newline='') as outfile:
    writer = csv.writer(outfile, delimiter='\t')
    # Write header
    writer.writerow(['transliterated_linear_b', 'greek'])
    
    # Example: copy original dataset to new file (you can modify this to include processing logic)
    for lb, greek_list in entries:
        writer.writerow([lb, "|".join(greek_list)])
