import json
from docx import Document

# Function to extract text from a DOCX file
def extract_text_from_docx(docx_path):
    try:
        doc = Document(docx_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip() != ""]
        return paragraphs
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return []

# Function to convert extracted text to JSON format
def convert_docx_to_json(docx_path, output_json_path):
    try:
        paragraphs = extract_text_from_docx(docx_path)
        
        # Convert the paragraphs to a structured dictionary
        data = {
            "file": docx_path,
            "content": paragraphs
        }
        
        # Save the content to a JSON file
        with open(output_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        
        print(f"✅ Conversion successful! Data saved to {output_json_path}.")
    
    except Exception as e:
        print(f"Error during conversion: {e}")

# Example usage
docx_path = "output_text.docx"  # Replace with your DOCX file path
output_json_path = "output.json"  # Desired output JSON file path

convert_docx_to_json(docx_path, output_json_path)
