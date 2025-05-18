import re

# Regex for first field: only lowercase letters, dashes, and * followed by 2 digits
field1_pattern = re.compile(r'^(?:[a-z\-]|(?:\*\d{2}))*$')

# Regex for second field: must NOT contain letters or digits
field2_pattern = re.compile(r'^[fh|\u03b1-\u03c9]+$')

# Path to your TSV file
file_path = 'cognates_final.cog'

with open(file_path, 'r', encoding='utf-8') as file:
    for line_num, line in enumerate(file, 1):
        fields = line.strip().split('\t')
        
        if len(fields) != 2:
            print(f"Line {line_num}: Incorrect number of fields")
            continue

        field1, field2 = fields

        if not field1_pattern.fullmatch(field1):
            print(f"Line {line_num}: Invalid first field: {field1}")
        
        if not field2_pattern.fullmatch(field2):
            print(f"Line {line_num}: Invalid second field: {field2}")
