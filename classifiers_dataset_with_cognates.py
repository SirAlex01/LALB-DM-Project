import pandas as pd

# Load the CSV and TSV files
classifiers_df = pd.read_csv("classifiers_dataset.csv")
cognates_df = pd.read_csv("cognates_final.cog", sep="\t")

# Merge on the Linear B field
merged_df = classifiers_df.merge(
    cognates_df,
    how="left",
    left_on="linear_b",
    right_on="transliterated_linear_b"
)

# Drop the 'transliterated_linear_b' column if not needed
merged_df = merged_df.drop(columns=["transliterated_linear_b"])

# Reorder columns to match desired output
output_df = merged_df[[
    "linear_b", "word_type", "part_of_speech", "inflection",
    "confidence", "greek", "reasoning"
]]

# Save the new file
output_df.to_csv("classifiers_dataset_with_cognates.csv", index=False)

print("Merged file saved as 'classifiers_dataset_with_cognates.csv'")
