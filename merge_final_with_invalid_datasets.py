import csv

# Carica i dati da cognates_final.cog in un dizionario
final_greek = {}
with open("cognates_final.cog", "r", encoding="utf-8") as f_final:
    reader = csv.DictReader(f_final, delimiter="\t")
    for row in reader:
        final_greek[row["transliterated_linear_b"]] = row["greek"]

# Campi completi e ridotti
full_fieldnames = ["transliterated_linear_b", "greek", "our_matching", "valid", "likelihood", "sequence_id"]
short_fieldnames = ["transliterated_linear_b", "greek"]

# Apri i file di output
with open("cognates.cog", "r", encoding="utf-8") as f_input, \
     open("cognates_with_invalid_full_data.cog", "w", encoding="utf-8", newline="") as f_full, \
     open("cognates_with_invalid.cog", "w", encoding="utf-8", newline="") as f_short:

    reader = csv.DictReader(f_input, delimiter="\t")
    writer_full = csv.DictWriter(f_full, fieldnames=full_fieldnames, delimiter="\t")
    writer_short = csv.DictWriter(f_short, fieldnames=short_fieldnames, delimiter="\t")

    writer_full.writeheader()
    writer_short.writeheader()

    for row in reader:
        translit = row["converted_linear_b"]
        new_matching = row["greek"]
        sequence_id = row["sequence_id"]
        valid = row["valid"]

        if translit in final_greek:
            greek_value = final_greek[translit]
            greek_words = len(greek_value.split("|"))
            likelihood = ("1.0|" * greek_words).rstrip("|")
        else:
            greek_value = row["gemini"]
            likelihood = row["likelihood"]

        full_row = {
            "transliterated_linear_b": translit,
            "greek": greek_value,
            "our_matching": new_matching,
            "valid": valid,
            "likelihood": likelihood,
            "sequence_id": sequence_id
        }

        short_row = {
            "transliterated_linear_b": translit,
            "greek": greek_value
        }

        writer_full.writerow(full_row)
        writer_short.writerow(short_row)

print("✅ File generati:")
print("- cognates_with_invalid_full_data.cog (completo)")
print("- cognates_with_invalid.cog (solo 2 colonne)")
