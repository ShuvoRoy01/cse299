import os
import csv
import re
import pandas as pd
from pypdf import PdfReader
from PIL import Image
from docx import Document
import pytesseract as tess
from fuzzywuzzy import fuzz
from transformers import MarianMTModel, MarianTokenizer

# Set Tesseract OCR Path
tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load MarianMT Translation Model for Bengali-to-English
model_name = "Helsinki-NLP/opus-mt-bn-en"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

# Input and output paths
input_directory = "E:\\pic to text\\pic"
output_csv_file = "output.csv"
merged_output_csv = "merged_output.csv"

# Function to detect Bengali text
def is_bengali(text):
    return any("\u0980" <= char <= "\u09FF" for char in text)  # Bengali Unicode Range

# Function to translate Bengali text to English
def translate_bengali_to_english(text):
    if not text.strip() or not is_bengali(text):
        return text  # Return original if not Bengali
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    translated = model.generate(**inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)

# Extract text from images
def extract_text_from_image(file_path):
    try:
        img = Image.open(file_path)
        return tess.image_to_string(img, lang="ben+eng")  # Bengali + English OCR
    except Exception as e:
        print(f"Error processing image {file_path}: {e}")
        return ""

# Extract text from PDF
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

# Extract text from DOCX
def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error processing DOCX {file_path}: {e}")
        return ""

# Extract structured rows
def extract_rows_from_text(text):
    rows = []
    patterns = [
        (r"(?P<label>[^:\n]+):\s*(?P<value>.*)"),  # `:` separator
        (r"(?P<label>[^:\n]+):-\s*(?P<value>.*)"),  # `:-` separator
        (r"(?P<label>[^ঃ\n]+)\s*ঃ\s*(?P<value>.*)"),  # Bengali `ঃ` separator
        (r"(?P<label>[^ঃ\n]+)\s*ঃ-\s*(?P<value>.*)")  # Bengali `ঃ-` separator
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            label = match.group("label").strip()
            value = match.group("value").strip()
            if is_bengali(label):
                translated_label = translate_bengali_to_english(label)
            else:
                translated_label = label  # Keep original if not Bengali
            rows.append((translated_label, value))

    return rows

try:
    all_labels = set()
    all_data = []

    # Step 1: Collect all unique labels
    for filename in os.listdir(input_directory):
        file_path = os.path.join(input_directory, filename)
        extracted_text = ""

        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            extracted_text = extract_text_from_image(file_path)
        elif filename.lower().endswith(".pdf"):
            extracted_text = extract_text_from_pdf(file_path)
        elif filename.lower().endswith(".docx"):
            extracted_text = extract_text_from_docx(file_path)

        if extracted_text:
            rows = extract_rows_from_text(extracted_text)
            for label, value in rows:
                all_labels.add(label)
                all_data.append((filename, label, value))

    all_labels = sorted(all_labels)

    # Step 2: Write extracted data to CSV
    with open(output_csv_file, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["Source"] + all_labels)

        for filename in os.listdir(input_directory):
            file_path = os.path.join(input_directory, filename)
            extracted_text = ""

            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                extracted_text = extract_text_from_image(file_path)
            elif filename.lower().endswith(".pdf"):
                extracted_text = extract_text_from_pdf(file_path)
            elif filename.lower().endswith(".docx"):
                extracted_text = extract_text_from_docx(file_path)

            row_data = {label: "" for label in all_labels}
            if extracted_text:
                rows = extract_rows_from_text(extracted_text)
                for label, value in rows:
                    row_data[label] = value

            writer.writerow([filename] + [row_data[label] for label in all_labels])

    print(f"Data successfully written to {output_csv_file}.")

    # Step 3: Load CSV and merge similar columns
    df = pd.read_csv(output_csv_file, encoding="utf-8-sig", encoding_errors="replace")

    def normalize_label(label):
        return label.replace("-", "").replace(" ", "").lower()

    def merge_similar_columns(df):
        columns = df.columns.tolist()
        merged_columns = set()
        similar_columns_dict = {}

        for col in columns:
            if col not in merged_columns:
                similar_columns = [col]
                for other_col in columns:
                    if col != other_col and fuzz.ratio(normalize_label(col), normalize_label(other_col)) > 80:
                        similar_columns.append(other_col)
                        merged_columns.add(other_col)

                if len(similar_columns) > 1:
                    similar_columns_dict[col] = similar_columns

        for base_col, similar_cols in similar_columns_dict.items():
            df[base_col] = df[similar_cols].apply(lambda row: ' '.join(row.dropna().astype(str)), axis=1)
            df.drop(columns=similar_cols[1:], inplace=True)

        return df

    df = merge_similar_columns(df)
    df.to_csv(merged_output_csv, encoding="utf-8-sig", index=False)
    print(f"Similar columns merged successfully. Data saved to {merged_output_csv}.")

except Exception as e:
    print(f"Error processing files: {e}")
