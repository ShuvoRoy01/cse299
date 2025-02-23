import json
import time
import google.generativeai as genai
import google.api_core.exceptions
import tkinter as tk
from tkinter import filedialog, simpledialog
import os

# Configure Google Gemini API (Replace 'YOUR_API_KEY' with your actual key)
genai.configure(api_key="AIzaSyDR0Lff5lZC5g5nfxddSjRpcG6ZJI6zXdo")

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
    model = genai.GenerativeModel("gemini-1.5-flash")  # Updated to use Gemini 1.5 Flash
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

# Step 1: Select JSON file
json_file_path = filedialog.askopenfilename(
    title="Select JSON file with persons",
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

# Retrieve list of persons
if "profiles" in data and isinstance(data["profiles"], list):
    persons = data["profiles"]
else:
    print("Error: JSON file does not contain a valid 'profiles' key.")
    exit(1)

# Step 2: Select TXT file containing forms
labels_file_path = filedialog.askopenfilename(
    title="Select TXT file with forms",
    filetypes=[("Text files", "*.txt")]
)
if not labels_file_path:
    print("No labels file selected. Exiting.")
    exit(1)

# Parse the TXT file into separate forms
try:
    with open(labels_file_path, "r", encoding="utf-8") as f:
        content = f.read()
except Exception as e:
    print(f"Error loading labels file: {e}")
    exit(1)

forms = []
sections = content.split("[START OF FORM]")
for section in sections:
    if "[END OF FORM]" in section:
        section_content = section.split("[END OF FORM]")[0].strip()
        lines = section_content.splitlines()
        if not lines:
            continue
        form_name = lines[0].strip()  # First line is the form name
        label_queries = [line.strip() for line in lines[1:] if line.strip()]
        forms.append({"name": form_name, "labels": label_queries})

if not forms:
    print("No valid forms found in the labels file. Exiting.")
    exit(1)

# Step 3: List available persons
print("Available persons:")
for idx, person in enumerate(persons, start=1):
    print(f"{idx}. {person.get('name', 'Unnamed')}")

# Ask the user to select a person
choice = simpledialog.askstring("Input", "Which person are you looking for? Enter the number:")
try:
    selected_index = int(choice) - 1
    selected_profile = persons[selected_index]
    selected_person = selected_profile.get("name", f"person_{selected_index+1}")
except (ValueError, IndexError):
    print("Invalid selection. Exiting.")
    exit(1)

# Step 4: List available forms
print("\nAvailable forms:")
for idx, form in enumerate(forms, start=1):
    print(f"{idx}. {form['name']}")

form_choice = simpledialog.askstring("Input", "Which form do you want to fill up? Enter the number:")
try:
    selected_form_index = int(form_choice) - 1
    selected_form = forms[selected_form_index]
except (ValueError, IndexError):
    print("Invalid selection. Exiting.")
    exit(1)

# Step 5: Match labels using Gemini and extract data
filled_data = {}
json_keys = list(selected_profile.keys())  # Get available keys in JSON

for query in selected_form["labels"]:
    prompt = (
        f"I have a label '{query}', and I need to find the most relevant key from the following options:\n"
        f"{json_keys}\n"
        "Return the closest match, or say 'Not found' if none are relevant."
    )

    matched_label = call_gemini(prompt)
    if matched_label and matched_label in selected_profile:
        filled_data[query] = selected_profile[matched_label]
    else:
        filled_data[query] = "Not found"

# Step 6: Save the filled form
output_filename = f"filled_form_{selected_form['name']}_{selected_person}.txt"
output_path = os.path.join(os.path.dirname(json_file_path), output_filename)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(f"Form Name: {selected_form['name']}\n")
    f.write(f"Person: {selected_person}\n")
    f.write("=" * 40 + "\n\n")
    for key, value in filled_data.items():
        f.write(format_nested_dict(key, value) + "\n\n")

print(f"✅ Filled form data saved to: {output_path}")
