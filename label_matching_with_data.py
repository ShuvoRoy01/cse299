import json
import time
import google.generativeai as genai
import google.api_core.exceptions  # For handling API errors
import tkinter as tk
from tkinter import filedialog

# Set up Google Gemini API (Replace 'YOUR_API_KEY' with your actual key)
genai.configure(api_key="AIzaSyBmuqdZc1uBK5TQHS323JVcVCuM-0Y48e0")  # Replace with your API key

# Dictionary to cache Gemini API responses for prompts
gemini_cache = {}

def load_json_file(file_path):
    """Load JSON file and handle errors."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("Error: The selected file is not a valid JSON file.")
        return None
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None

def call_gemini(prompt):
    """Call Gemini 1.5 Flash API with caching and exponential backoff."""
    # Use cached response if available.
    if prompt in gemini_cache:
        return gemini_cache[prompt]
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    retries = 3
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            gemini_cache[prompt] = response.text  # Cache the result
            return response.text
        except google.api_core.exceptions.ResourceExhausted:
            # Exponential backoff: wait longer each retry
            wait_time = 15 * (attempt + 1)
            print(f"Quota exceeded! Retrying in {wait_time} seconds... ({attempt + 1}/{retries})")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    print("Error: Exceeded API quota or encountered an error. Try again later.")
    return None

def match_labels_with_gemini(labels_dict, data_dict):
    """
    Recursively match keys from labels_dict with data_dict using Gemini API.
    For each key in labels_dict, ask Gemini to find the best matching key in data_dict.
    """
    matched = {}
    for label_key, label_val in labels_dict.items():
        # For nested dictionaries, if the key exists in data and is a dict, do recursion.
        if isinstance(label_val, dict):
            if label_key in data_dict and isinstance(data_dict[label_key], dict):
                nested_match = match_labels_with_gemini(label_val, data_dict[label_key])
                if nested_match:
                    matched[label_key] = nested_match
            else:
                # If the nested key is not found directly, try Gemini on the full data.
                prompt = (
                    f"Given the following JSON data: {json.dumps(data_dict, indent=2)}\n\n"
                    f"Find the best matching key for the nested label '{label_key}'. "
                    "Return only the key exactly as it appears in the JSON."
                )
                gemini_response = call_gemini(prompt)
                if gemini_response:
                    candidate = gemini_response.strip()
                    if candidate in data_dict and isinstance(data_dict[candidate], dict):
                        nested_match = match_labels_with_gemini(label_val, data_dict[candidate])
                        if nested_match:
                            matched[candidate] = nested_match
        else:
            # For simple (non-dict) labels, ask Gemini to find the best matching key.
            prompt = (
                f"Given the following JSON data: {json.dumps(data_dict, indent=2)}\n\n"
                f"Find the best matching key for the label '{label_key}' and return the key exactly as it appears in the JSON."
            )
            gemini_response = call_gemini(prompt)
            if gemini_response:
                candidate = gemini_response.strip()
                # Check if candidate matches any key (case-insensitive)
                for key in data_dict.keys():
                    if key.lower() == candidate.lower():
                        matched[label_key] = data_dict[key]
                        break
    return matched

# Initialize Tkinter and hide the root window.
root = tk.Tk()
root.withdraw()

# Select the JSON file containing the data with values.
print("Select the JSON file containing the data:")
data_json_path = filedialog.askopenfilename(
    title="Select Data JSON file",
    filetypes=[("JSON files", "*.json")]
)
if not data_json_path:
    print("No data file selected. Exiting.")
    exit(1)

# Select the JSON file containing the labels.
print("Select the JSON file containing the labels:")
labels_json_path = filedialog.askopenfilename(
    title="Select Labels JSON file",
    filetypes=[("JSON files", "*.json")]
)
if not labels_json_path:
    print("No labels file selected. Exiting.")
    exit(1)

# Load both JSON files.
data_json = load_json_file(data_json_path)
labels_json = load_json_file(labels_json_path)

if data_json is None or labels_json is None:
    print("Error loading JSON files. Exiting.")
    exit(1)

# Debug: Print loaded JSON structures.
print("Loaded Data JSON:")
print(json.dumps(data_json, indent=2))
print("\nLoaded Labels JSON:")
print(json.dumps(labels_json, indent=2))

# Use Gemini API to match labels from the labels JSON in the data JSON.
matched_output = match_labels_with_gemini(labels_json, data_json)

# Save the matched labels to an output JSON file.
output_json_path = filedialog.asksaveasfilename(
    title="Save Matched Labels JSON",
    defaultextension=".json",
    filetypes=[("JSON files", "*.json")]
)
if output_json_path:
    try:
        with open(output_json_path, "w", encoding="utf-8") as outfile:
            json.dump(matched_output, outfile, indent=2, ensure_ascii=False)
        print(f"Matched labels saved to {output_json_path}")
    except Exception as e:
        print(f"Error saving output file: {e}")
else:
    print("No output file selected. Exiting.")
