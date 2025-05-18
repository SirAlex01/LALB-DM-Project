import re

# Regex for first field: only lowercase letters, dashes, and * followed by 2 digits
field1_pattern = re.compile(r'^(?:[a-z\-]|(?:\*\d{2}))*$')

# Regex for second field: must NOT contain letters or digits
field2_pattern = re.compile(r'^[fh|\u03b1-\u03c9]+$')

# Set to track seen field1 values
seen_field1 = set()

# Path to your TSV file
file_path = 'cognates_final.cog'

with open(file_path, 'r', encoding='utf-8') as file:
    for line_num, line in enumerate(file, 1):
        fields = line.strip().split('\t')
        
        if len(fields) != 2:
            print(f"Line {line_num}: Incorrect number of fields")
            continue

        field1, field2 = fields

        # Check for duplicate words in field1 (| separated)
        words1 = field1.split('|')
        if len(words1) != len(set(words1)):
            print(f"Line {line_num}: Duplicate words in first field: {field1}")
        
        # Check for duplicate words in field2 (| separated)
        words2 = field2.split('|')
        if len(words2) != len(set(words2)):
            print(f"Line {line_num}: Duplicate words in second field: {field2}")

        # Validate each word in field1 individually
        for w in words1:
            if not field1_pattern.fullmatch(w):
                print(f"Line {line_num}: Invalid word in first field: {w}")

        # Validate entire field2
        if not all(field2_pattern.fullmatch(w) for w in words2):
            print(f"Line {line_num}: Invalid word(s) in second field: {field2}")

        # Check for duplicate full field1 entry
        if field1 in seen_field1:
            print(f"Line {line_num}: Duplicate full first field entry: {field1}")
        else:
            seen_field1.add(field1)
