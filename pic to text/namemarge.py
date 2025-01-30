import pandas as pd
from fuzzywuzzy import fuzz

# Load the CSV file into a DataFrame
df = pd.read_csv('output.csv')

# Function to find the most likely column that contains names
def get_name_column(df):
    for col in df.columns:
        # Check if the column contains string data which is likely to be names
        if df[col].dtype == 'object':
            return col
    return None  # If no such column exists

# Function to merge similar rows based on fuzzy matching
def merge_similar_rows(df, name_column, threshold=85):
    """
    Merge rows with similar names based on fuzzy matching.
    
    :param df: DataFrame containing the data
    :param name_column: The column containing the names to compare
    :param threshold: The similarity threshold for matching (0-100)
    :return: Modified DataFrame with merged similar rows
    """
    rows_to_merge = []
    
    # Iterate through the DataFrame and compare each name with others
    for i, row in df.iterrows():
        if i in rows_to_merge:  # Skip already merged rows
            continue
        
        # Compare current row's name with all subsequent rows
        for j, row2 in df.iloc[i+1:].iterrows():
            similarity = fuzz.ratio(row[name_column], row2[name_column])
            
            if similarity >= threshold:
                # Merge rows (e.g., combine the 'address' or other fields)
                df.loc[i, 'address'] = str(row['address']) + ' ' + str(row2['address'])  # Example for combining addresses
                
                # Mark the second row for removal after merging
                rows_to_merge.append(j)

    # Remove the merged rows
    df = df.drop(rows_to_merge).reset_index(drop=True)
    
    # After merging, drop duplicates based on the merged names
    df.drop_duplicates(subset=[name_column], inplace=True)

    return df

# Find the column that likely contains the names
name_column = get_name_column(df)

if name_column:
    print(f"Found name column: {name_column}")
    # Apply the merging function
    df = merge_similar_rows(df, name_column)  # Use the dynamically found name column

    # Save the merged data to a new CSV file
    df.to_csv('merged_file.csv', index=False)
    print("CSV file processed and saved as 'merged_file.csv'")
else:
    print("No suitable name column found.")
