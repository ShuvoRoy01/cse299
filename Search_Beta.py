import json
import time
import google.generativeai as genai
import google.api_core.exceptions  # Import this to handle API errors
import tkinter as tk
from tkinter import filedialog, simpledialog

# Set up Google Gemini API (Replace 'YOUR_API_KEY' with your actual key)
genai.configure(api_key="AIzaSyA5NsarKaBHTnF2Rx0aQJP4wd1jcRrONjs")

def format_nested_dict(key, value):
    """Formats a nested dictionary into a bullet-pointed string."""
    if isinstance(value, dict):
        formatted = f"{key}:-\n"
        for sub_key, sub_value in value.items():
            formatted += f"# {sub_key}: {sub_value}\n"
        return formatted.strip()
    return f"{key}: {value}"

# Initialize Tkinter and hide the root window.
root = tk.Tk()
root.withdraw()

# Open a file chooser dialog to let the user select a JSON file.
json_file_path = filedialog.askopenfilename(
    title="Select JSON file with persons",
    filetypes=[("JSON files", "*.json")]
)

if not json_file_path:
    print("No file selected. Exiting.")
    exit(1)

# Load the JSON data with UTF-8 encoding.
try:
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
except json.JSONDecodeError:
    print("Error: The selected file is not a valid JSON file. Exiting.")
    exit(1)
except Exception as e:
    print(f"Error loading JSON file: {e}")
    exit(1)

# Retrieve the list of persons.
if "profiles" in data and isinstance(data["profiles"], list):
    persons = data["profiles"]
else:
    print("Error: JSON file does not contain a valid 'profiles' key.")
    exit(1)

def call_gemini(prompt):
    """Retries Gemini API call if quota is exceeded."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    retries = 3  # Number of retries
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except google.api_core.exceptions.ResourceExhausted:
            wait_time = 10  # Wait 10 seconds before retrying
            print(f"Quota exceeded! Retrying in {wait_time} seconds... ({attempt + 1}/{retries})")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    print("Error: Exceeded API quota. Try again later.")
    return None

while True:
    # List all available persons.
    print("\nAvailable persons:")
    for index, person in enumerate(persons, start=1):
        print(f"{index}. {person['name']}")
    
    # Prompt the user for person selection.
    choice = simpledialog.askstring("Input", "Which one are you? Enter the number:")
    
    try:
        selected_index = int(choice) - 1
        selected_profile = persons[selected_index]
        selected_person = selected_profile["name"]
    except (ValueError, IndexError):
        print("Invalid selection. Try again.")
        continue
    
    initial_question = (
        f"You are an AI assistant. The JSON file contains multiple persons. "
        f"Detected person: {selected_person}. "
        "List all labels (keys) available in the JSON file for this person."
    )
    
    initial_response = call_gemini(initial_question)
    if initial_response:
        print("\nInitial Response from model:")
        print(initial_response)
    
    while True:
        # Ask the user for the label they want to search.
        label_query = simpledialog.askstring("Input", "Enter the label you want to search for:")
        if not label_query:
            print("No label entered. Restarting selection.")
            break  # Restart from person selection
        
        second_question = (
            f"Based on the following JSON data for {selected_person}:{json.dumps(selected_profile, indent=2)}\n\n"
            f"Find the most relevant label that matches or is similar to '{label_query}'. "
            f"For example, if the user searches for 'birth place', but the actual label is 'place_of_birth', return 'place_of_birth' and its value. "
            f"Provide the best-matching label and value in a clear, formatted manner."
        )
        
        second_response = call_gemini(second_question)
        if second_response:
            print("\nResponse for label query from model:")
            print(second_response)
        
        found = False
        for key, value in selected_profile.items():
            if label_query.lower() in key.lower():
                found = True
                formatted_output = format_nested_dict(key, value)
                print(f"\n{formatted_output}\n")
        
        if not found:
            print("Label not found. Try again.")
