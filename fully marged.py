import pandas as pd
import spacy
from fuzzywuzzy import fuzz

# Load spaCy model for semantic similarity
nlp = spacy.load("en_core_web_md")

# Input / Output CSV Files
input_csv = "output.csv"
merged_csv = "merged_output.csv"

# Normalize Column Names for Better Matching
def normalize_label(label):
    return label.strip().replace("-", "").replace(" ", "").lower()

# Function to Merge Similar Columns Based on SpaCy Similarity
def merge_similar_columns(df, fuzzy_threshold=85, spacy_threshold=0.75):
    columns = df.columns.tolist()
    merged_columns = set()
    similar_columns_dict = {}

    # Identify similar columns based on fuzzy matching and SpaCy semantic similarity
    for col in columns:
        if col not in merged_columns:
            similar_columns = [col]
            doc1 = nlp(col)  # Using spaCy to create the vector representation for col
            for other_col in columns:
                if col != other_col and other_col not in merged_columns:
                    # Fuzzy matching first
                    if fuzz.ratio(normalize_label(col), normalize_label(other_col)) > fuzzy_threshold:
                        similar_columns.append(other_col)
                        merged_columns.add(other_col)
                    else:
                        # If fuzzy matching is not enough, use spaCy for semantic similarity
                        doc2 = nlp(other_col)
                        similarity = doc1.similarity(doc2)
                        if similarity >= spacy_threshold:
                            similar_columns.append(other_col)
                            merged_columns.add(other_col)

            if len(similar_columns) > 1:
                similar_columns_dict[col] = similar_columns

    # Merge data in similar columns
    for base_col, similar_cols in similar_columns_dict.items():
        valid_cols = [col for col in similar_cols if col in df.columns]
        # Merge columns by combining their non-null values into one column
        df[base_col] = df[valid_cols].fillna("").apply(lambda row: ' '.join(row.astype(str)).strip(), axis=1)
        df.drop(columns=valid_cols[1:], inplace=True, errors="ignore")

    return df

try:
    # Step 1: Read CSV
    df = pd.read_csv(input_csv, encoding="utf-8-sig", keep_default_na=False)

    # Step 2: Print All Column Names Before Merging
    print("📌 Original Columns:", list(df.columns))

    # Step 3: Merge Similar Columns with Updated Thresholds
    df = merge_similar_columns(df, fuzzy_threshold=85, spacy_threshold=0.75)  # Adjust thresholds here

    # Step 4: Print All Column Names After Merging
    print("✅ Merged Columns:", list(df.columns))

    # Step 5: Save Merged CSV
    df.to_csv(merged_csv, encoding="utf-8-sig", index=False)
    print(f"✅ Merged CSV saved as {merged_csv}.")

except Exception as e:
    print(f"❌ Error: {e}")
