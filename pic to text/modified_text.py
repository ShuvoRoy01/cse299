import pandas as pd
from fuzzywuzzy import fuzz, process

# Load the CSV file
df = pd.read_csv("output.csv")

# Function to merge columns with similar names
def merge_similar_columns(df):
    columns = df.columns.tolist()

    # Create a list to store columns that are already merged
    merged_columns = []

    # Create a dictionary to hold similar columns (grouped by similarity)
    similar_columns_dict = {}

    for col in columns:
        if col not in merged_columns:
            similar_columns = [col]
            for other_col in columns:
                if col != other_col and fuzz.ratio(col.lower(), other_col.lower()) > 80:  # Threshold for similarity
                    similar_columns.append(other_col)
                    merged_columns.append(other_col)  # Mark the column as merged

            if len(similar_columns) > 1:
                similar_columns_dict[col] = similar_columns

    # Now we need to merge data from similar columns
    for base_col, similar_cols in similar_columns_dict.items():
        # Merge the data from the similar columns
        df[base_col] = df[similar_cols].apply(lambda row: ' '.join(row.dropna().astype(str)), axis=1)
        
        # Drop the similar columns (we keep only the base column)
        df.drop(columns=similar_cols[1:], inplace=True)

    return df

# Apply the function to merge similar columns
df = merge_similar_columns(df)

# Save the updated CSV with merged columns
df.to_csv("merged_output.csv", index=False)

print("Similar columns merged successfully.")
