import csv
'''
# Define input and output files
input_file = "Linear-B-Lexicon.csv"
output_file = "cleaned.csv"

# Relevant column headers (normalize spacing)
wanted_headers = [
    "Transliteration (Latin)",
    "Pronunciation (Greek)",
    "Pronunciation (English)",
    "Translation (English)"
]

with open(input_file, newline='', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    
    # Normalize headers
    fieldnames = [name.strip() for name in reader.fieldnames]
    
    # Map original headers to stripped versions
    header_map = {name.strip(): name for name in reader.fieldnames}
    
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=wanted_headers)
        writer.writeheader()
        
        for row in reader:
            cleaned_row = {header: row.get(header_map.get(header, ""), "").strip() for header in wanted_headers}
            if any(cleaned_row.values()):  # Skip completely empty rows
                writer.writerow(cleaned_row)

#whitespaces, "

#for greek
# -


#example weird transformation
# po-ni-ke-(j)a/ po-ni-ki-ja/po-ni-ki-jo,φοινίκια/ φοινίκιος,phoinikia/ phoinikios,cnmson

#"ke-ra/ ke-ra-a2/ ke-ra-e/ ke-ra(-ja)/-i-ja ke-ra-ja-pi",κέρας/ κέραhα,keras/ keraha,horn (implying the material)
'''

import csv

input_file = 'cleaned.csv'    # Replace with your input file name
output_file = 'dataset.csv'  # Output file to write cleaned data

with open(input_file, mode='r', newline='', encoding='utf-8') as infile, \
     open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
    
    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    header = next(reader)  # Read header
    writer.writerow(header)

    for row in reader:
        # Clean first two fields
        row[0] = row[0].replace('"', '').replace("'", '').replace("to2", "tyo").replace("ro2", "ryo").replace("si2", "*64").replace("sa2", "*82").replace("ra3", "rai").replace("ra2", "rya").replace("pu2", "phu").replace("ta2","tya").replace("a3", "ai").replace("a2", "ha")
        row[1] = row[1].replace('"', '').replace("'", '').replace(" ", "")
        writer.writerow(row)
