import csv
import unicodedata
import json
from clean_gemini_output import normalize_greek_word, correction_dict, allowed_chars

def apply_corrections_to_jsonl(input_file, output_file):
    """Apply corrections to a JSONL file with Linear B analysis"""
    corrections_made = []
    words_with_bad_chars = 0
    still_problematic = 0
    total_entries = 0
    
    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:
        
        for line in infile:
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                total_entries += 1
                
                # Process each Linear B word entry
                for linear_b_key, analysis in data.items():
                    if isinstance(analysis, dict) and "output" in analysis:
                        # Check if this entry has any cognates with bad characters (count once per entry)
                        entry_has_bad_chars = False
                        
                        # Process each cognate in the output list
                        for cognate_entry in analysis["output"]:
                            if isinstance(cognate_entry, dict) and "cognate" in cognate_entry:
                                cognate_field = cognate_entry["cognate"]
                                
                                # Check if original field has bad characters (for entry-level counting)
                                original_bad_chars = {ch for ch in cognate_field if ch not in allowed_chars}
                                if original_bad_chars and not entry_has_bad_chars:
                                    entry_has_bad_chars = True
                                    words_with_bad_chars += 1
                                
                                # Apply corrections
                                corrected_cognate = normalize_greek_word(cognate_field, linear_b_key)
                                
                                # Track corrections made
                                if cognate_field != corrected_cognate:
                                    corrections_made.append((linear_b_key, cognate_field, corrected_cognate))
                                
                                # Update the cognate field
                                cognate_entry["cognate"] = corrected_cognate
                                
                                # Check for remaining bad characters
                                bad_chars = {ch for ch in corrected_cognate if ch not in allowed_chars}
                                if bad_chars:
                                    still_problematic += 1
                                    print(f"Still problematic in key {linear_b_key}: {''.join(sorted(bad_chars))} {corrected_cognate}")
                
                # Write the corrected JSON line
                outfile.write(json.dumps(data, ensure_ascii=False) + "\n")
                
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON line: {e}")
                continue
    
    return {
        'total_entries': total_entries,
        'words_with_bad_chars': words_with_bad_chars,
        'corrections_made': len(corrections_made),
        'still_problematic': still_problematic,
        'corrections_list': corrections_made
    }

def apply_corrections_to_file(input_file, output_file, delimiter="\t"):
    """Apply all corrections to a file and save as a new file"""
    corrections_made = []
    words_with_bad_chars = 0
    still_problematic = 0
    total_rows = 0
    
    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8", newline='') as outfile:
        
        reader = csv.DictReader(infile, delimiter=delimiter)
        
        # Only process files with 'gemini' column
        if "gemini" not in reader.fieldnames:
            raise ValueError(f"File {input_file} must have a 'gemini' column. Found columns: {reader.fieldnames}")
        
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames, delimiter=delimiter)
        writer.writeheader()
        
        for row in reader:
            total_rows += 1
            gemini_field = row["gemini"]
            linear_b_key = row[reader.fieldnames[0]]  # First column is the Linear B key
            
            # Check if original field has bad characters
            original_bad_chars = {ch for ch in gemini_field if ch not in allowed_chars}
            if original_bad_chars:
                words_with_bad_chars += 1
            
            # Split by | to handle multiple words
            words = gemini_field.split('|')
            corrected_words = []
            
            for word in words:
                original_word = word
                corrected_word = normalize_greek_word(word, linear_b_key)
                corrected_words.append(corrected_word)
                
                # Track corrections made
                if original_word != corrected_word:
                    corrections_made.append((linear_b_key, original_word, corrected_word))
            
            # Update ONLY the gemini field with corrected words
            row["gemini"] = '|'.join(corrected_words)
            
            # Check for any remaining bad characters after correction
            corrected_field = row["gemini"]
            bad_chars = {ch for ch in corrected_field if ch not in allowed_chars}
            if bad_chars:
                still_problematic += 1
                print(f"Still problematic in key {linear_b_key}: {''.join(sorted(bad_chars))} {corrected_field}")
            
            # Write the corrected row
            writer.writerow(row)
    
    # Return statistics
    return {
        'total_rows': total_rows,
        'words_with_bad_chars': words_with_bad_chars,
        'corrections_made': len(corrections_made),
        'still_problematic': still_problematic,
        'corrections_list': corrections_made
    }

def main():
    files_to_process = [
        ("cognates_translation.cog", "cognates_translation_corrected.cog", "cog"),
        ("gemini_output_translation.jsonl", "gemini_output_translation_corrected.jsonl", "jsonl"),
        # Only process files that have AI-generated content that needs correction
    ]
    
    print("APPLYING CORRECTIONS TO AI-GENERATED CONTENT...")
    print("=" * 60)
    
    for input_file, output_file, file_type in files_to_process:
        try:
            print(f"\nProcessing: {input_file} -> {output_file} ({file_type.upper()})")
            
            if file_type == "cog":
                stats = apply_corrections_to_file(input_file, output_file)
                target_field = "'gemini' column"
            elif file_type == "jsonl":
                stats = apply_corrections_to_jsonl(input_file, output_file)
                target_field = "'cognate' fields"
            else:
                print(f"Unknown file type: {file_type}")
                continue
            
            print(f"Successfully processed {input_file}")
            print(f"   Total entries: {stats.get('total_rows', stats.get('total_entries', 0))}")
            print(f"   Target field: {target_field}")
            print(f"   Words with bad characters: {stats['words_with_bad_chars']}")
            print(f"   Total corrections made: {stats['corrections_made']}")
            print(f"   Still problematic: {stats['still_problematic']}")
            
            if stats['still_problematic'] == 0:
                print(f"   {output_file} is 100% compliant with character set!")
            else:
                print(f"   {stats['still_problematic']} entries still have issues")
                
        except FileNotFoundError:
            print(f"File not found: {input_file} - skipping")
        except Exception as e:
            print(f"Error processing {input_file}: {e}")
    
    print("\nCORRECTION PROCESS COMPLETED!")
    print("\nCorrected files created:")
    for input_file, output_file, file_type in files_to_process:
        print(f"  - {output_file}")

if __name__ == "__main__":
    main()
