import os
import csv
import re
import pandas as pd
from pypdf import PdfReader
from PIL import Image
from docx import Document
import pytesseract as tess
from fuzzywuzzy import fuzz

# Set Tesseract OCR Path
tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Input and output paths
input_directory = "E:\\pic to text\\pic"  # Directory containing images, PDFs, and DOCX
output_csv_file = "output.csv"  # Output CSV file
merged_output_csv = "merged_output.csv"  # Output file with merged columns

# Function to extract text from an image
def extract_text_from_image(file_path):
    try:
        img = Image.open(file_path)
        return tess.image_to_string(img)
    except Exception as e:
        print(f"Error processing image {file_path}: {e}")
        return ""

# Function to extract text from a PDF
def extract_text_from_pdf(file_path):
    try:
        text = ""
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error processing PDF {file_path}: {e}")
        return ""

# Function to extract text from a DOCX file
def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error processing DOCX {file_path}: {e}")
        return ""

# Function to extract structured rows from text using regex
def extract_rows_from_text(text):
    try:
        rows = []
        # Pattern for `:` separator
        pattern_colon = r"(?P<label>[^:\n]+):\s*(?P<value>.*)"
        matches_colon = re.finditer(pattern_colon, text)
        for match in matches_colon:
            label = match.group('label').strip()
            value = match.group('value').strip()
            rows.append((label, value))

        # Pattern for `:-` separator
        pattern_dash_colon = r"(?P<label>[^:\n]+):-\s*(?P<value>.*)"
        matches_dash_colon = re.finditer(pattern_dash_colon, text)
        for match in matches_dash_colon:
            label = match.group('label').strip()
            value = match.group('value').strip()
            rows.append((label, value))

        return rows
    except Exception as e:
        print(f"Error extracting rows: {e}")
        return []

# Process all files in the input directory
try:
    all_labels = set()
    all_data = []

    # First pass: Collect all unique labels
    for filename in os.listdir(input_directory):
        file_path = os.path.join(input_directory, filename)
        extracted_text = ""

        # Determine file type and extract text
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            extracted_text = extract_text_from_image(file_path)
        elif filename.lower().endswith(".pdf"):
            extracted_text = extract_text_from_pdf(file_path)
        elif filename.lower().endswith(".docx"):
            extracted_text = extract_text_from_docx(file_path)

        # Extract rows from the text
        if extracted_text:
            rows = extract_rows_from_text(extracted_text)
            for label, value in rows:
                all_labels.add(label)
                all_data.append((filename, label, value))

    # Write extracted data to CSV with dynamic column headers
    all_labels = sorted(all_labels)
    with open(output_csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Write header row
        writer.writerow(["Source"] + all_labels)

        # Write data rows
        for filename in os.listdir(input_directory):
            file_path = os.path.join(input_directory, filename)
            extracted_text = ""

            # Determine file type and extract text
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                extracted_text = extract_text_from_image(file_path)
            elif filename.lower().endswith(".pdf"):
                extracted_text = extract_text_from_pdf(file_path)
            elif filename.lower().endswith(".docx"):
                extracted_text = extract_text_from_docx(file_path)

            # Extract rows from the text
            row_data = {label: "" for label in all_labels}
            if extracted_text:
                rows = extract_rows_from_text(extracted_text)
                for label, value in rows:
                    row_data[label] = value

            # Write row to CSV
            writer.writerow([filename] + [row_data[label] for label in all_labels])

    print(f"Data successfully written to {output_csv_file}.")

    # Load CSV for column merging
    df = pd.read_csv(output_csv_file)

    # Normalize label by removing hyphens for comparison
    def normalize_label(label):
        return label.replace('-', '').lower()

    # Function to merge similar columns
    def merge_similar_columns(df):
        columns = df.columns.tolist()
        merged_columns = []  # Track already merged columns
        similar_columns_dict = {}

        # Create a dictionary for columns with similar labels based on fuzzy matching
        for col in columns:
            if col not in merged_columns:
                similar_columns = [col]
                for other_col in columns:
                    if col != other_col and fuzz.ratio(normalize_label(col), normalize_label(other_col)) > 80:
                        similar_columns.append(other_col)
                        merged_columns.append(other_col)

                if len(similar_columns) > 1:
                    similar_columns_dict[col] = similar_columns

        # Merge data from similar columns
        for base_col, similar_cols in similar_columns_dict.items():
            df[base_col] = df[similar_cols].apply(lambda row: ' '.join(row.dropna().astype(str)), axis=1)
            df.drop(columns=similar_cols[1:], inplace=True)

        return df

    # Apply column merging
    df = merge_similar_columns(df)

    # Save final cleaned CSV
    df.to_csv(merged_output_csv, index=False)
    print(f"Similar columns merged successfully. Data saved to {merged_output_csv}.")

except Exception as e:
    print(f"Error processing files: {e}")
