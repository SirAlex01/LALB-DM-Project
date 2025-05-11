import csv
# put in a list each line of the cognates file
def parse_tsv(file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        data = [row for row in reader]
    return data

luo = parse_tsv("converted_linear_b-greek.cog")
luo_words = set([dic['converted_linear_b'] for dic in luo])

ours = parse_tsv("corrected_cognates.cog")

for dic in ours:
    if bool(int(dic['valid'])) and dic['converted_linear_b'] not in luo_words:
        likelihoods = dic['likelihood'].split("|")     
        greek_words = dic['gemini'].split("|")
        good_ones = []
        for l, g in zip(likelihoods, greek_words):
            l = float(l)
            if l >= 0.75:
                good_ones.append(g)
        if len(good_ones) > 0:
            luo.append({'converted_linear_b': dic['converted_linear_b'], 'greek': "|".join(good_ones)})
                
luo = sorted(luo, key = lambda x:x["converted_linear_b"])

def write_tsv(file_path, rows):
    if not rows or not isinstance(rows, list):
        raise ValueError("Empty or invalid data provided.")

    # Rename 'converted_linear_b' to 'transliterated_linear_b' in all rows
    updated_rows = []
    for row in rows:
        new_row = dict(row)  # Copy the original row
        if 'converted_linear_b' in new_row:
            new_row['transliterated_linear_b'] = new_row.pop('converted_linear_b')
        updated_rows.append(new_row)

    # Set the correct field names
    field_names = ['transliterated_linear_b', 'greek']

    # Write to the file
    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=field_names, delimiter='\t')
        writer.writeheader()
        for row in updated_rows:
            writer.writerow(row)

write_tsv("cognates_dataset.cog", luo)           