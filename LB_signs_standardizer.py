import csv
import os

# Paths to the input and output CSV files
SIGNS_LB = "signs_LB.csv"
SEQUENCES_LB = "sequences_LB.csv"
OUTPUT_SIGNS_FILE = "processed_signs_LB.csv"
OUTPUT_SEQUENCES_FILE = "processed_sequences_LB.csv"

def preprocess(s):
    return s.replace("₂", "2").replace("₃", "3").replace("TU+RO2", "TU+RYO").replace("A2","HA").replace("A3","AI")\
            .replace("pu2","phu").replace("ro2","ryo").replace("ra2", "rya").replace("ra3", "rai").replace("ta2", "tya")\
            .replace("a2","ha").replace("a3","ai")

# Process the signs_LB.csv
with open(SIGNS_LB, mode='r', newline='', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    
    # Open the output CSV file for writing
    with open(OUTPUT_SIGNS_FILE, mode='w', newline='', encoding='utf-8') as outfile:
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Process each row in signs_LB.csv
        for row in reader:
            sign = row['sign']  # Store the 'sign' column in a variable
            processed_sign = preprocess(sign)
            row['sign'] = processed_sign  # Add the processed result
            
            # Write the updated row to the output CSV
            writer.writerow(row)

print("Signs file processing complete. File saved as:", OUTPUT_SIGNS_FILE)

# Process the sequences_LB.csv
with open(SEQUENCES_LB, mode='r', newline='', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    
    # Open the output CSV file for writing
    with open(OUTPUT_SEQUENCES_FILE, mode='w', newline='', encoding='utf-8') as outfile:
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Process each row in sequences_LB.csv
        for row in reader:
            sequence = row['sequence']  # Store the 'sequence' column in a variable
            sequence = sequence.split("-")
            for i, s in enumerate(sequence):
                sequence[i] = preprocess(s)
            row['sequence'] = "-".join(sequence)  # Add the processed result
            
            # Write the updated row to the output CSV
            writer.writerow(row)

print("Sequences file processing complete. File saved as:", OUTPUT_SEQUENCES_FILE)
