import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load the CSV file
file_path = "E:\pic to text\\merged_output.csv"  # Change this to your file path
df = pd.read_csv(file_path)

# Function to normalize text (remove special characters, lowercase)
def clean_text(text):
    # Remove all non-alphanumeric characters except spaces, to preserve Bangla characters
    text = re.sub(r'[^a-zA-Z0-9\u0980-\u09FF\s]', '', text)  # Including Unicode range for Bangla characters
    return text.lower().strip()

# Get cleaned column names
cleaned_columns = [clean_text(col) for col in df.columns]

# Compute TF-IDF similarity
vectorizer = TfidfVectorizer().fit_transform(cleaned_columns)
similarity_matrix = cosine_similarity(vectorizer)

# Threshold for considering columns as similar
threshold = 0.75
column_groups = {}

# Group similar columns
for i in range(len(cleaned_columns)):
    for j in range(i + 1, len(cleaned_columns)):
        if similarity_matrix[i, j] >= threshold:
            if df.columns[i] not in column_groups:
                column_groups[df.columns[i]] = set()
            column_groups[df.columns[i]].add(df.columns[j])
            column_groups[df.columns[i]].add(df.columns[i])

# Merge similar columns
for main_col, similar_cols in column_groups.items():
    merged_data = df[list(similar_cols)].astype(str).apply(lambda x: ', '.join(x.dropna().unique()), axis=1)
    df.drop(columns=[col for col in similar_cols if col in df.columns], inplace=True)
    df[main_col] = merged_data

# Save cleaned CSV
output_file = "cleaned_data.csv"
df.to_csv(output_file, index=False)

print(f"✅ Merged similar columns and saved as '{output_file}'")
