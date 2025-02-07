import ollama
import json
import tkinter as tk
from tkinter import filedialog

def upload_json():
    """Open a file dialog to upload a JSON file."""
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window

    file_path = filedialog.askopenfilename(
        title="Select a JSON file",
        filetypes=[("JSON files", "*.json")]
    )

    return file_path

def process_json_with_llama(file_path):
    """Process the JSON file using Llama 3.2 3B and extract labeled data."""
    try:
        # 🔹 Load JSON file with UTF-8 encoding
        with open(file_path, "r", encoding="utf-8-sig") as file:
            json_data = json.load(file)

        # 🔹 Convert JSON to text for Llama, preserving non-ASCII characters like Bangla
        input_text = "Extract structured and labeled information from the following JSON data:\n" + json.dumps(json_data, ensure_ascii=False, indent=2)

        # 🔹 Call Llama 3.2 3B using Ollama
        response = ollama.chat(model="llama3.2:3b", messages=[{
    "role": "system",
    "content": """
        You are a powerful AI that extracts structured and labeled information from raw JSON data.
        The data may contain a mix of English and Bangla text. Your task is to:
        
        1. Identify and extract key pieces of structured information, such as full name, student ID, date of birth, blood group, program, and contact details.
        2. Match the extracted fields to predefined labels (e.g., 'full_name', 'student_id', 'date_of_birth', etc.).
        3. Output the extracted data in a well-structured JSON format, similar to:
            {
                "full_name": "John Doe",
                "student_id": "12345",
                "date_of_birth": "1990-01-01",
                "blood_group": "O+",
                "program": "Computer Science"
            }
        4. Make sure to handle variations in naming conventions and fields (e.g., 'DOB' vs 'date_of_birth') and map them correctly.
        5. If some fields are missing or unrecognizable, label them as 'N/A' (not available).
        6. If multiple instances of data are present, return an array of objects with each entry corresponding to one set of extracted information.

        The JSON data you will process may contain other fields or variations in formatting, so apply your best judgment to extract and label the relevant information correctly. If you are unsure, output 'N/A' for that field.

        Example of a processed output:

        {
            "full_name": "John Doe",
            "student_id": "12345",
            "date_of_birth": "1990-01-01",
            "blood_group": "O+",
            "program": "Computer Science"
        }
    """
}, {
    "role": "user",
    "content": input_text
}])


        # 🔍 Print the full response for debugging
        print("🔍 Full Response from Model:", response)

        # 🔹 Check if response is a dictionary and contains 'message'
        if isinstance(response, dict) and 'message' in response:
            # Extract the content from the message object directly
            extracted_data = response['message'].content  # Access 'content' directly

            # 🔹 If the extracted data is a string, clean it up (strip)
            if isinstance(extracted_data, str):
                extracted_data = extracted_data.strip()

            # 🔹 Try to convert extracted_data to a JSON-like structure for clean output
            # Assuming extracted_data is a structured string, let's break it into dictionary format
            try:
                structured_data = json.loads(extracted_data)
            except json.JSONDecodeError:
                # If parsing fails, we treat it as a plain text (structure can be done manually)
                structured_data = {"extracted_text": extracted_data}

            # 🔹 Save the processed data as a clean JSON file
            output_path = "processed_data.json"
            with open(output_path, "w", encoding="utf-8") as out_file:
                json.dump(structured_data, out_file, ensure_ascii=False, indent=2)

            print(f"✅ Processed JSON saved at: {output_path}")

        else:
            print("❌ Response doesn't contain 'message' or is not in the expected format.")

    except Exception as e:
        print(f"❌ Error processing JSON: {e}")

if __name__ == "__main__":
    # 🔹 Upload JSON file
    json_file_path = upload_json()

    if json_file_path:
        # 🔹 Process JSON with Llama 3.2 3B
        process_json_with_llama(json_file_path)
    else:
        print("❌ No file selected.")
