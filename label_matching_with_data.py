import json
import time
import tkinter as tk
from tkinter import filedialog
import google.generativeai as genai
import google.api_core.exceptions  # For handling API errors

# Configure Gemini API (Replace 'YOUR_API_KEY' with your actual key)
genai.configure(api_key="AIzaSyA5NsarKaBHTnF2Rx0aQJP4wd1jcRrONjs")

def format_nested_dict(key, value):
    """Formats a nested dictionary into a bullet-pointed string."""
    if isinstance(value, dict):
        formatted = f"{key}:-\n"
        for sub_key, sub_value in value.items():
            formatted += f"# {sub_key}: {sub_value}\n"
        return formatted.strip()
    return f"{key}: {value}"

def extract_labels(data, labels_list):
    """Recursively extracts all labels from a nested JSON structure."""
    if isinstance(data, dict):
        for key, value in data.items():
            labels_list.append(key)
            extract_labels(value, labels_list)
    elif isinstance(data, list):
        for item in data:
            extract_labels(item, labels_list)

def call_gemini(prompt):
    """Calls the Gemini API to get the best-matching label."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    retries = 3  # Number of retries
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except google.api_core.exceptions.ResourceExhausted:
            wait_time = 15 # Wait 10 seconds before retrying
            print(f"Quota exceeded! Retrying in {wait_time} seconds... ({attempt + 1}/{retries})")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    print("Error: Exceeded API quota. Try again later.")
    return None

def search_and_extract_data(label, data, output_file):
    """Searches for a label in the data and extracts its value if found."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == label:
                formatted_output = format_nested_dict(key, value)
                output_file.write(formatted_output + "\n\n")
            else:
                search_and_extract_data(label, value, output_file)
    elif isinstance(data, list):
        for item in data:
            search_and_extract_data(label, item, output_file)

# Initialize Tkinter and hide the root window.
root = tk.Tk()
root.withdraw()

# Open a file chooser dialog to let the user select the labels-only JSON file.
labels_json_path = filedialog.askopenfilename(
    title="Select JSON file with labels only",
    filetypes=[("JSON files", "*.json")]
)

if not labels_json_path:
    print("No labels JSON file selected. Exiting.")
    exit(1)

# Open a file chooser dialog to let the user select the JSON file with labels and data.
data_json_path = filedialog.askopenfilename(
    title="Select JSON file with labels and data",
    filetypes=[("JSON files", "*.json")]
)

if not data_json_path:
    print("No data JSON file selected. Exiting.")
    exit(1)

# Load the labels-only JSON data.
try:
    with open(labels_json_path, "r", encoding="utf-8") as f:
        labels_data = json.load(f)
except json.JSONDecodeError:
    print("Error: The selected labels file is not a valid JSON file. Exiting.")
    exit(1)
except Exception as e:
    print(f"Error loading labels JSON file: {e}")
    exit(1)

# Load the JSON data with labels and their corresponding data.
try:
    with open(data_json_path, "r", encoding="utf-8") as f:
        data_with_values = json.load(f)
except json.JSONDecodeError:
    print("Error: The selected data file is not a valid JSON file. Exiting.")
    exit(1)
except Exception as e:
    print(f"Error loading data JSON file: {e}")
    exit(1)

# Extract all labels from the labels-only JSON file.
labels_list = []
extract_labels(labels_data, labels_list)

# Open a text file to write the extracted data.
output_file_path = "extracted_data.txt"
with open(output_file_path, "w", encoding="utf-8") as output_file:
    # Use Gemini to find the best-matching label and extract its value.
    for label in labels_list:
        # Create a prompt for Gemini to find the best-matching label in the data JSON.
        prompt = (
            f"Given the following JSON data:\n{json.dumps(data_with_values, indent=2)}\n\n"
            f"Find the best-matching label for '{label}' in the JSON data. "
            f"Return the label and its corresponding value in a clear, formatted manner."
        )
        
        # Call Gemini to get the best-matching label and value.
        gemini_response = call_gemini(prompt)
        if gemini_response:
            output_file.write(f"Label: {label}\n")
            output_file.write(f"Best Match and Value:\n{gemini_response}\n\n")
        else:
            output_file.write(f"Label: {label}\n")
            output_file.write("No matching label found.\n\n")

print(f"Data extraction complete. Extracted data saved to {output_file_path}")
