import csv

# Allowed characters
allowed_chars = set("fhαβγδεζηθικλμνξοπρςστυφχψω|")

def check_greek_characters(path, delimiter="\t"):
    words_with_bad_chars = 0
    
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if "gemini" not in reader.fieldnames:
            raise ValueError("File must have a 'gemini' column")

        for row in reader:
            greek_field = row["gemini"]
            bad_chars = {ch for ch in greek_field if ch not in allowed_chars}
            if bad_chars:
                words_with_bad_chars += 1
                print(f"⚠️ Problem in key {row[reader.fieldnames[0]]}: {''.join(sorted(bad_chars))} {greek_field}")
    
    print(f"\n📊 STATISTICS:")
    print(f"Words with bad characters: {words_with_bad_chars}")

if __name__ == "__main__":
    check_greek_characters("cognates_translation.cog")
    check_greek_characters("cognates_translation_corrected.cog")
