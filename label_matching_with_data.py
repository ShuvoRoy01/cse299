import json
import time
import google.generativeai as genai
import google.api_core.exceptions
import tkinter as tk
from tkinter import filedialog
import os
from difflib import get_close_matches

# Configure Google Gemini API (Replace 'YOUR_API_KEY' with your actual key)
genai.configure(api_key="AIzaSyBmuqdZc1uBK5TQHS323JVcVCuM-0Y48e0")

def format_nested_dict(key, value):
    """Formats a nested dictionary into a structured string."""
    if isinstance(value, dict):
        formatted = f"{key}:\n"
        for sub_key, sub_value in value.items():
            formatted += f"  - {sub_key}: {sub_value}\n"
        return formatted.strip()
    return f"{key}: {value}"

def call_gemini(prompt):
    """Calls Gemini 1.5 Flash to find the best matching label."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    retries = 3  # Number of retries in case of API failure
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except google.api_core.exceptions.ResourceExhausted:
            wait_time = 15
            print(f"Quota exceeded! Retrying in {wait_time} seconds... ({attempt + 1}/{retries})")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    print("Error: Exceeded API quota. Try again later.")
    return None

# Initialize Tkinter and hide the root window
root = tk.Tk()
root.withdraw()

# Step 1: Select JSON file containing data
json_file_path = filedialog.askopenfilename(
    title="Select JSON file with data",
    filetypes=[("JSON files", "*.json")]
)
if not json_file_path:
    print("No file selected. Exiting.")
    exit(1)

# Load JSON data
try:
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
except json.JSONDecodeError:
    print("Error: Invalid JSON file. Exiting.")
    exit(1)
except Exception as e:
    print(f"Error loading JSON file: {e}")
    exit(1)

# Step 2: Select JSON file containing labels
labels_file_path = filedialog.askopenfilename(
    title="Select JSON file with labels",
    filetypes=[("JSON files", "*.json")]
)
if not labels_file_path:
    print("No labels file selected. Exiting.")
    exit(1)

# Load labels JSON
try:
    with open(labels_file_path, "r", encoding="utf-8") as f:
        labels_json = json.load(f)
except json.JSONDecodeError:
    print("Error: Invalid labels JSON file. Exiting.")
    exit(1)
except Exception as e:
    print(f"Error loading labels JSON file: {e}")
    exit(1)

# Extract labels (if JSON is a dict, use keys; if it's a list, use the list)
if isinstance(labels_json, dict):
    labels_list = list(labels_json.keys())
elif isinstance(labels_json, list):
    labels_list = labels_json
else:
    print("Error: Labels JSON file format is incorrect.")
    exit(1)

# Step 3: Match labels using Gemini and fallback fuzzy matching, then extract data
filled_data = {}
json_keys = list(data.keys())  # Available keys in the data JSON

for query in labels_list:
    # Prepare prompt for Gemini
    prompt = (
        f"I have a label '{query}'. From the following options:\n"
        f"{json_keys}\n"
        "Identify the key that best corresponds in meaning to the label. "
        "Respond with the exact key name if a match is found, or respond with 'Not found' if no match is appropriate."
    )

    matched_label = call_gemini(prompt)
    # Check if the Gemini response is valid and exists in data
    if matched_label and matched_label in data:
        print(f"Gemini matched '{query}' to '{matched_label}'.")
        filled_data[query] = data[matched_label]
    else:
        # Fallback: use fuzzy matching (difflib) if Gemini does not yield a valid key
        fallback_matches = get_close_matches(query, json_keys, n=1, cutoff=0.6)
        if fallback_matches:
            fallback_label = fallback_matches[0]
            print(f"Fallback matched '{query}' to '{fallback_label}'.")
            filled_data[query] = data[fallback_label]
        else:
            print(f"No match found for '{query}'.")
            filled_data[query] = "Not found"

# Step 4: Save the extracted data to a text file
output_filename = "matched_labels_output.txt"
output_path = os.path.join(os.path.dirname(json_file_path), output_filename)

with open(output_path, "w", encoding="utf-8") as f:
    f.write("Extracted Data Based on Labels\n")
    f.write("=" * 40 + "\n\n")
    for key, value in filled_data.items():
        f.write(format_nested_dict(key, value) + "\n\n")

print(f"✅ Extracted data saved to: {output_path}")
