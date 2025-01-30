import pandas as pd

# Load the CSV file into a DataFrame
df = pd.read_csv('output.csv')

# Print all the column names (labels) to see what we are working with
print("Column labels from CSV:", df.columns)

# Iterate through each column and print its data
for column in df.columns:
    print(f"\nData for '{column}' label:")
    print(df[column].to_string(index=False))

# Example: If you want to insert the data into a new file where each row is represented by its labels:
with open('extracted_data.txt', 'w') as f:
    # Write the column headers as the first line
    f.write("\t".join(df.columns) + "\n")  # Separate labels with a tab for clarity
    
    # Iterate through each row and write its data under the corresponding labels
    for index, row in df.iterrows():
        f.write("\t".join(str(value) for value in row) + "\n")

print("Data has been extracted and saved to 'extracted_data.txt'.")
