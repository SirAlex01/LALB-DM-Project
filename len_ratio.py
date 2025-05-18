def compute_avg_ratio_from_tsv(file_path):
    total_ratio = 0
    count = 0

    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()

    # Skip the header
    for line in lines[1:]:
        line = line.strip()
        if not line or '\t' not in line:
            continue

        latin, greek = line.split('\t')
        linb_len = latin.count('-') + 1

        greek_variants = greek.split('|')
        avg_greek_len = sum(len(g) for g in greek_variants) / len(greek_variants)

        ratio = avg_greek_len / linb_len
        total_ratio += ratio
        count += 1

        print(f"{latin} -> Avg Greek Len: {avg_greek_len:.2f}, Linb Len: {linb_len}, Ratio: {ratio:.2f}")

    print(f"\nTotal Pairs: {count}")
    print(f"Accumulated Ratio Sum: {total_ratio:.2f}")
    print(f"Average Ratio: {total_ratio / count:.4f}" if count else "No valid entries found.")

# Example usage
compute_avg_ratio_from_tsv("cognates_final.cog")

