import os
import re
from PIL import Image
import pytesseract as tess

# Set Tesseract OCR Path (Modify this path if needed)
tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Function to extract text from an image using Tesseract OCR
def extract_text_from_image(file_path):
    try:
        img = Image.open(file_path)
        text = tess.image_to_string(img)
        return text
    except Exception as e:
        print(f"Error processing image {file_path}: {e}")
        return ""

# Function to extract key-value pairs from the processed text using regex
def extract_key_value_pairs(text):
    # Example: Regex to handle various delimiters like ":", "-", or "/"
    pattern = r"(?P<label>[^:\-\n/]+)[\:\-\s/]+(?P<value>[^:\-\n/]+)"
    
    # Finding all matches for labels and values
    matches = re.finditer(pattern, text)
    
    key_value_pairs = {}
    for match in matches:
        label = match.group("label").strip()
        value = match.group("value").strip()
        key_value_pairs[label] = value

    return key_value_pairs

# Test with an image (change the file path to the image you want to analyze)
file_path = "E:\pic to text\pic\56926ec0-3fd0-4c03-a608-f5c4754d2f27.jpg"  # Replace with your image path

# Extract text from the image
extracted_text = extract_text_from_image(file_path)

# Print the raw extracted text (you can modify this to analyze the image content)
print("Extracted Text from Image:")
print(extracted_text)

# Extract key-value pairs from the text using regex
key_value_pairs = extract_key_value_pairs(extracted_text)

# Print the extracted key-value pairs (labels and values)
print("\nExtracted Key-Value Pairs:")
for label, value in key_value_pairs.items():
    print(f"{label}: {value}")
