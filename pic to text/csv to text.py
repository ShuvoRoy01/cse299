import csv
import re

# Path to the CSV file
csv_file = "output.csv"
updated_csv_file = "updated_output.csv"  # New file with additional columns

# Regex patterns to identify Name, Age, and Email
name_pattern = r"Name:\s*([A-Za-z\s]+)"  # Looks for "Name: " followed by text
age_pattern = r"Age:\s*(\d+)"            # Looks for "Age: " followed by digits
email_pattern = r"Email:\s*([\w\.-]+@[\w\.-]+\.\w+)"  # Email regex

try:
    # Open the original file for reading
    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        header = next(reader)  # Read the header row

        # Add new fields to the header
        updated_header = header + ["Name", "Age", "Email"]

        # Open the new file for writing
        with open(updated_csv_file, mode="w", newline="", encoding="utf-8") as updated_file:
            writer = csv.writer(updated_file)
            writer.writerow(updated_header)  # Write updated header

            # Process each row in the original CSV
            for row in reader:
                extracted_text = row[1]  # Assuming the extracted text is in the second column

                # Extract Name, Age, and Email using regex
                name_match = re.search(name_pattern, extracted_text)
                age_match = re.search(age_pattern, extracted_text)
                email_match = re.search(email_pattern, extracted_text)

                # Get the extracted values or leave them blank if not found
                name = name_match.group(1) if name_match else ""
                age = age_match.group(1) if age_match else ""
                email = email_match.group(1) if email_match else ""

                # Append the new fields to the row
                updated_row = row + [name, age, email]
                writer.writerow(updated_row)  # Write the updated row

    print(f"Data with extracted fields has been saved to {updated_csv_file}.")
except FileNotFoundError:
    print(f"The file {csv_file} does not exist.")
except Exception as e:
    print(f"Error processing the file: {e}")
