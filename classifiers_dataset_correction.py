import csv

# Define input and output paths
input_path = 'classifiers_dataset_old.csv'
output_path = 'classifiers_dataset.csv'

# Open the input file and the output file
with open(input_path, mode='r', newline='', encoding='utf-8') as infile, \
     open(output_path, mode='w', newline='', encoding='utf-8') as outfile:

    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    # Optional: process header
    header = next(reader)
    writer.writerow(header)  # write the header as is, or modify it

    # Process each line
    for row in reader:
        # Example processing: strip whitespace from all fields
        processed_row = []
        for i, field in enumerate(row):
            field = field.strip() if i not in range(1, 5) else int(field.strip()) if i != 4 else float(field.strip())
            if i == 1:
                if field < 3:
                    field = 0
                else:
                    field -= 2
            processed_row.append(field)
        
        writer.writerow(processed_row)
