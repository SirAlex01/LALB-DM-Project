import csv
import argparse

def load_csv_as_dict(path, delimiter="\t"):
    """
    Load a CSV/TSV into a dictionary.
    Key = first column
    Value = dict of remaining columns
    """
    result = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        fieldnames = reader.fieldnames
        if not fieldnames:
            return result, []  # empty file

        for row in reader:
            key = row[fieldnames[0]].strip()
            if not key:
                continue
            # build list of the other fields
            value = {field: row[field].strip() for field in fieldnames[1:]}
            result[key] = value

    return result, fieldnames

def print_dicts_overview(name1, dict1, fields1, name2, dict2, fields2):
    """
    Print an overview comparing the keys and fieldnames of two dictionaries.
    """
    keys1 = set(dict1.keys())
    keys2 = set(dict2.keys())

    intersection = keys1 & keys2
    only_in_1 = keys1 - keys2
    only_in_2 = keys2 - keys1

    print(f"Len {name1}: {len(keys1)}")
    print(f"Len {name2}: {len(keys2)}")
    print(f"Intersection: {len(intersection)}")
    print(f"Only in {name1} (first - second): {len(only_in_1)}")
    print(f"Only in {name2} (second - first): {len(only_in_2)}")
    print(f"Fieldnames of {name1}: {fields1}")
    print(f"Fieldnames of {name2}: {fields2}")


def merge_datasets(out_file, dict1, dict2, fields1, fields2, fields1_mapping=None, fields2_mapping=None, delimiter="\t"):
    """
    Merge two dictionaries by combining their values.
    """
    if fields1_mapping is None:
        fields1_mapping = {f: f for f in fields1}  # identity mapping for all fields in the first dict
    if fields2_mapping is None:
        fields2_mapping = {f: f for f in fields2}  # identity mapping for all fields in the second dict

    assert len(fields1_mapping) == len(fields1), "fields1_mapping must cover all fields in fields1"
    assert len(fields2_mapping) == len(fields2), "fields2_mapping must cover all fields in fields2"

    out_fields = [fields2_mapping[f] for f in fields2]
    for f in fields1:
        mapped_f = fields1_mapping[f]
        if mapped_f not in out_fields:
            out_fields.append(mapped_f)
    print(f"Output fields: {out_fields}")
    inv_fields1_mapping = {v: k for k, v in fields1_mapping.items()}
    inv_fields2_mapping = {v: k for k, v in fields2_mapping.items()}

    def deal_with_field(key, field, dict1, dict2, out_fields, fields1_mapping, fields2_mapping):
        if field in {"transliterated_linear_b"}:
            return key

        if key in dict1 and key in dict2:
            if field in {"greek"}:
                return dict1[key][fields1_mapping[field]]
            elif field in {"our_matching", "sequence_id", "completeness_level"}:
                return dict2[key][fields2_mapping[field]]
            elif field in {"likelihood"}:
                greek_value = dict1[key][fields1_mapping["greek"]]
                greek_words = len(greek_value.split("|"))
                return ("1.0|" * greek_words).rstrip("|")
        
        elif key in dict1:
            if field in {"greek"}:
                return dict1[key][fields1_mapping[field]]
            elif field in {"completeness_level"}:
                return "COMPLETE"
            elif field in {"likelihood"}:
                greek_value = dict1[key][fields1_mapping["greek"]]
                greek_words = len(greek_value.split("|"))
                return ("1.0|" * greek_words).rstrip("|")
            else:
                return None
            
        elif key in dict2:
            if field in {"likelihood", "greek"}:
                val = dict2[key][fields2_mapping[field]]
                likelihood_values = dict2[key][fields2_mapping["likelihood"]]
                if "|" in likelihood_values:
                    likelihood_values = likelihood_values.split("|")
                    values = val.split("|")
                    assert len(likelihood_values) == len(values), f"Mismatch in number of values for key {key}"
                    ans = []
                    for i, lv in enumerate(likelihood_values):
                        try:
                            lv = float(lv)
                            if lv >= 0.7:
                                ans.append(values[i])
                            if len(ans) == 0:
                                max_val = sorted(range(len(values)), key=lambda idx: float(likelihood_values[idx]), reverse=True)[0]
                                ans.append(values[max_val])
                        except ValueError:
                            print(f"Warning: Non-numeric likelihood '{lv}' for key {key}")
                    if field == "greek":
                        print(key, values, likelihood_values, ans)
                    return "|".join(ans)
            return dict2[key][fields2_mapping[field]]
        
        print(f"Warning: key {key} not found in either dictionary when processing field {field}")
        return None

    out_file_full = "".join(out_file.split(".")[:-1]) + "_full_data." + out_file.split(".")[-1]
    short_fields = out_fields[:2]
    with open(out_file_full, "w", encoding="utf-8", newline="") as f_out:
        with open(out_file, "w", encoding="utf-8", newline="") as f_out_short:
            # writers for full and short
            writer_full = csv.DictWriter(f_out, fieldnames=out_fields, delimiter=delimiter)
            writer_short = csv.DictWriter(f_out_short, fieldnames=short_fields, delimiter=delimiter)

            writer_full.writeheader()
            writer_short.writeheader()

            all_keys = sorted(set(dict1.keys()) | set(dict2.keys()))
            print(f"Merging {len(all_keys)} entries...")

            for key in all_keys:
                row = {}
                for field in out_fields:
                    row[field] = deal_with_field(
                        key, field, dict1, dict2, out_fields, inv_fields1_mapping, inv_fields2_mapping
                    )

                # write full row
                writer_full.writerow(row)

                # write short row with only first 2 fields
                short_row = {f: row[f] for f in short_fields}
                writer_short.writerow(short_row)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Compare two cognates TSVs.")
    ap.add_argument("--first", required=True, help="Path to first file (e.g., cognates_final.cog)")
    ap.add_argument("--second", required=True, help="Path to second file (e.g., cognates_translation.cog)")
    ap.add_argument("--output", required=True, help="Path to output file (e.g., merged.cog)")
    ap.add_argument("--delimiter", default="\t", help="Delimiter used in the input files")
    args = ap.parse_args()
    assert args.first != args.second, "Input files must be different"
    
    dict1, fields1 = load_csv_as_dict(args.first, args.delimiter)
    dict2, fields2 = load_csv_as_dict(args.second, args.delimiter)

    fields1_mapping = None
    fields2_mapping = None

    if args.second in {"cognates_translation.cog", "cognates_translation_corrected.cog"}:
        fields2[1], fields2[2] = fields2[2], fields2[1] # swap the two fields
        fields2_mapping = {f: f for f in fields2}
        fields2_mapping["converted_linear_b"] = "transliterated_linear_b"
        fields2_mapping["greek"] = "our_matching"
        fields2_mapping["gemini"] = "greek"
    

    print_dicts_overview(args.first, dict1, fields1, args.second, dict2, fields2)
    merge_datasets(args.output, dict1, dict2, fields1, fields2, fields1_mapping=fields1_mapping, fields2_mapping=fields2_mapping, delimiter=args.delimiter)
