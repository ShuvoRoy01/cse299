import os
import csv
from pypdf import PdfReader
from PIL import Image
from docx import Document
import pytesseract as tess
import re

# Set Tesseract OCR Path
tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Input and output paths
input_directory = "E:\\pic to text\\pic"  # Directory containing images and PDFs
output_csv_file = "output.csv"  # Output CSV file

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
            text += page.extract_text()
        return text.strip()
    except Exception as e:
        print(f"Error processing PDF {file_path}: {e}")
        return ""

# Function to extract rows from text based on :- or -
def extract_rows_from_text(text):
    try:
        rows = []
        pattern = r"(?P<label>[^:\n]+)[:-]\s*(?P<value>.*)"
        matches = re.finditer(pattern, text)
        for match in matches:
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

        # Check if the file is an image
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            extracted_text = extract_text_from_image(file_path)

        # Check if the file is a PDF
        elif filename.lower().endswith(".pdf"):
            extracted_text = extract_text_from_pdf(file_path)

        # Extract rows from the text
        if extracted_text:
            rows = extract_rows_from_text(extracted_text)
            for label, value in rows:
                all_labels.add(label)
                all_data.append((filename, label, value))

    # Write to CSV with dynamic column headers
    all_labels = sorted(all_labels)
    with open(output_csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Write header row
        writer.writerow(["Source"] + all_labels)

        # Write data rows
        for filename in os.listdir(input_directory):
            file_path = os.path.join(input_directory, filename)
            extracted_text = ""

            # Check if the file is an image
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                extracted_text = extract_text_from_image(file_path)

            # Check if the file is a PDF
            elif filename.lower().endswith(".pdf"):
                extracted_text = extract_text_from_pdf(file_path)

            # Extract rows from the text
            row_data = {label: "" for label in all_labels}
            if extracted_text:
                rows = extract_rows_from_text(extracted_text)
                for label, value in rows:
                    row_data[label] = value

            # Write row to CSV
            writer.writerow([filename] + [row_data[label] for label in all_labels])

    print(f"Data successfully written to {output_csv_file}.")
except Exception as e:
    print(f"Error processing files: {e}")