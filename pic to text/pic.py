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
input_directory = "E:\pic to text\pic"  # Directory containing images and PDFs
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

# Function to extract name from text
def extract_name(text):
    try:
        # Use regex to find the line containing "Name"
        match = re.search(r"?P<label>[^:\n]+)[:-]\s*(?P<value>.*", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()  # Extract and clean the name
        return "Not Found"  # Return this if no name is found
    except Exception as e:
        print(f"Error extracting name: {e}")
        return "Error"

# Process all files in the input directory
try:
    with open(output_csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(['Source', 'Extracted Text', 'Name'])  # Header row with an additional Name column

        for filename in os.listdir(input_directory):
            file_path = os.path.join(input_directory, filename)
            extracted_text = ""
            name = ""

            # Check if the file is an image
            if filename.lower().endswith((".png", ".jpg", ".jpeg",".webp")):
                print(f"Processing image: {filename}")
                extracted_text = extract_text_from_image(file_path)

            # Check if the file is a PDF
            elif filename.lower().endswith(".pdf"):
                print(f"Processing PDF: {filename}")
                extracted_text = extract_text_from_pdf(file_path)

            # Extract the name from the text
            if extracted_text:
                name = extract_name(extracted_text)

            # Write extracted text and name to CSV
            writer.writerow([filename, extracted_text, name])

    print(f"Data successfully written to {output_csv_file}.")
except Exception as e:
    print(f"Error processing files: {e}")
