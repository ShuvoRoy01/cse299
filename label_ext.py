import os
import glob
import time
import json
import re
import google.generativeai as genai
from PIL import Image
from pdf2image import convert_from_path
from docx2pdf import convert as docx2pdf_convert
from fpdf import FPDF
import tkinter as tk
from tkinter import filedialog
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# ============================
# API key
# ============================
API_KEY = "AIzaSyBmuqdZc1uBK5TQHS323JVcVCuM-0Y48e0"
genai.configure(api_key=API_KEY)

# ============================
# Initializing the Gemini model
# ============================
model = genai.GenerativeModel("gemini-1.5-flash")

# ============================
# Directory user input and defining supported file types
# ============================
root = tk.Tk()
root.withdraw()
print("Select the folder containing the files")
INPUT_FOLDER = filedialog.askdirectory(title="Select the folder containing the files")
if not INPUT_FOLDER:
    print("No folder selected. Exiting.")
    exit(1)

image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
docx_exts = {".docx"}
txt_exts = {".txt"}
pdf_exts = {".pdf"}

# ============================
# Poppler Path
# ============================
poppler_path = r"C:\\Users\\User\\AppData\\Roaming\\Microsoft\\Windows\\Network Shortcuts\\Release-24.07.0-0\\poppler-24.07.0\\Library\\bin"

converted_images = []

# ============================
# Convert PDF to Images
# ============================
def convert_pdf_to_images(pdf_path):
    try:
        images = convert_from_path(pdf_path, dpi=200, poppler_path=poppler_path)
        base_name = os.path.splitext(pdf_path)[0]
        for idx, image in enumerate(images, start=1):
            output_filename = f"{base_name}-{idx}.jpg"
            image.save(output_filename, "JPEG")
            converted_images.append(output_filename)
        print(f"Converted '{pdf_path}' to {len(images)} image(s).")
    except Exception as e:
        print(f"Error converting PDF '{pdf_path}': {e}")

# ============================
# Convert DOCX to Images
# ============================
def convert_docx_to_images(docx_path):
    try:
        pdf_path = os.path.splitext(docx_path)[0] + ".pdf"
        docx2pdf_convert(docx_path, os.path.dirname(docx_path))
        convert_pdf_to_images(pdf_path)
        os.remove(pdf_path)
    except Exception as e:
        print(f"Error converting DOCX '{docx_path}': {e}")

# ============================
# Convert TXT to Images
# ============================
def convert_txt_to_images(txt_path):
    try:
        pdf_path = os.path.splitext(txt_path)[0] + ".pdf"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font("Arial", size=12)

        with open(txt_path, "r", encoding="utf-8-sig") as file:
            for line in file:
                pdf.multi_cell(0, 10, line)

        pdf.output(pdf_path)
        convert_pdf_to_images(pdf_path)
        os.remove(pdf_path)
    except Exception as e:
        print(f"Error converting TXT '{txt_path}': {e}")

# ============================
# Process Files
# ============================
def process_files():
    files = glob.glob(os.path.join(INPUT_FOLDER, "*"))
    for file_path in files:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in pdf_exts:
            convert_pdf_to_images(file_path)
        elif ext in docx_exts:
            convert_docx_to_images(file_path)
        elif ext in txt_exts:
            convert_txt_to_images(file_path)

# ============================
# Extract Text from Images
# ============================
def extract_text_from_images():
    all_files = glob.glob(os.path.join(INPUT_FOLDER, "*"))
    aggregated_text = ""

    for file_path in all_files:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in image_exts:
            try:
                img = Image.open(file_path)
            except Exception as e:
                print(f"Error opening image {file_path}: {e}")
                continue

            ocr_prompt = (
                "Read each and every line of the file carefully "
                "extract all the possible text from the file "
            )

            try:
                response = model.generate_content([ocr_prompt, img])
                file_text = response.text.strip()
            except Exception as e:
                print(f"Error extracting text from image {file_path}: {e}")
                continue

            img.close()
            time.sleep(5)

            aggregated_text += f"--- Filename: {os.path.basename(file_path)} ---\n{file_text}\n\n"

    return aggregated_text

# ============================
# Extract Labels from Web Form
# ============================
def extract_labels_from_web_form(url):
    options = Options()
    options.headless = True  
    options.add_argument("--disable-blink-features=AutomationControlled")  
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    extracted_labels = ""

    try:
        driver.set_page_load_timeout(60)
        driver.get(url)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.TAG_NAME, 'form')))

        soup = BeautifulSoup(driver.page_source, "html.parser")
        questions = soup.select('div[role="heading"]')
        labels = [q.get_text(strip=True) for q in questions]
        extracted_labels = "\n".join(labels)

        print(f" Extracted labels from Google Form.")

    except Exception as e:
        print(f" Error extracting from web form: {e}")
    finally:
        driver.quit()

    return extracted_labels

def clean_json_response(response_text):
    """
    Cleans and extracts valid JSON from Gemini's response.
    Removes unwanted characters like ```json and ensures proper formatting.
    """
    response_text = response_text.strip()

    # Remove ```json and ``` if they exist
    response_text = re.sub(r"^```json", "", response_text)  # Remove opening ```json
    response_text = re.sub(r"```$", "", response_text)  # Remove closing ```
    
    # Ensure it is a valid JSON format
    try:
        json.loads(response_text)  # Test if it's valid JSON
    except json.JSONDecodeError:
        print(" Invalid JSON format detected, returning empty JSON.")
        return '{"labels": []}'  # Return a default valid JSON

    return response_text

# ============================
# Generate JSON Profile
# ============================
def generate_json_profile(aggregated_text):
    """
    Sends extracted text to Gemini for structured JSON output.
    Uses retries and ensures valid JSON formatting.
    """
    profile_prompt = f"""
Context:-You are an AI specialized in extracting and structuring form labels into a valid JSON format. There can be multiple file your task is to accurately extract **only the labels and check list that i have to fill up (field names) from the given form** and return the result in a **strictly valid JSON format**.
         There might be cases where there will be examples given inside a field of how to fill up that field. You need to understand that. Distinguish between example inside a field and labels.just extract the labels that I need to fill up dont extact extra text.

Example:- 
          input:-
          2. Research publications and achievements in Last 10 Years (2015 -Till) 
            [ Full point for First Author or Corresponding Author; point will be proportional for other cases]

           a. Article Publication in Reported Journal:
            (i) Article in Web of Science indexed Journal with Impact Factor; Q1/Q2 Preferable
               i. [Article Full Citation, IF, Q?] – [Role as First Author/Corresponding Author/ Supervisor/ Co-Author]
               ii. [Article Full Citation IF, Q?] – [Role as First Author/Corresponding Author/ Supervisor/ Co-Author]

            (ii) Article in Scopus indexed Journal excluding publications mentioned in (i); Q1/Q2 Preferable
               i. [Article Full Citation, Q?] – [Role as First Author/Corresponding Author/ Supervisor/ Co-Author]
               ii. [Article Full Citation, Q?] – [Role as First Author/Corresponding Author/ Supervisor/ Co-Author]

            b. Book Publication for CSE/IT Tertiary Level
               i. [Book Name] – [Authors Name] – [Publisher & Year] – [Your Involvement]
               ii. [Book Name] – [Authors Name] – [Publisher & Year] – [Your Involvement]

              
        How the proccess has done (contextual information):- it is extracting all the labels as the user need to fill up. And here the first necessary field is a label and then in the next line there is another 
        necessary label which is a subclass of the previous detected label.Now what you have to do is in the output json set those labels as subclass which you think that should be a subclass of the previous extarcted label.
        Don't repeat the same extracted label twice. if you think there is a same label is extracting twice you should mention its previous class label. 

            output:-
            -Specific Experience
               -Research Publications and Achievements (2015 - Till)
                 -Article Publication in Indexed Journals
                    -Web of Science Indexed Journals with Impact Factor
                    -Scopus Indexed Journals
                    -Citation details, Impact Factor, Q-Rank, Role (First Author/Corresponding Author/ Supervisor/Co-Author)

                 -Book Publication for CSE/IT Tertiary Level
                    -Book Name 
                    -Authors Name 
                    -Publisher & Year
                    -Your Involvement              


Example 2:- 
context:- if there is any checklist available then extract all of them.

   input:-  
       Do you agree to the Department communicating with you by email or other electronic means?
           (checklist)☐ No
           (checklist)☐ Yes
           If Yes, please provide your email address: [___________]      


output:-
{{
 "Do you agree to the Department communicating with you by email or other electronic means?",
  "options": [
    "No",
    "Yes"
  ],
  "email_field": "If Yes, please provide your email address"
}}


example 3:-
input:- Applicants 16 years of age or over must provide a current document with a photograph and/or signature.
       Acceptable documents include:
       (checklist)☐ Australian driver’s licence
       (checklist)☐ Passport
       (checklist)☐ United Nations High Commissioner for Refugees (UNHCR) document
       (checklist)☐ National identity card
       (checklist)☐ Other document containing both a signature and photograph, such as:
          
  output(json):-  
  {{
  "requirement": "Applicants 16 years of age or over must provide a current document with a photograph and/or signature.",
  "acceptable_documents": [
    "Australian driver’s licence",
    "Passport",
    "United Nations High Commissioner for Refugees (UNHCR) document",
    "National identity card",
    "Other document containing both a signature and photograph, such as:",
    
  ]
}}
     
      


<<<
{aggregated_text}
>>>
"""

    retry_attempts = 3
    json_output = {}

    for attempt in range(retry_attempts):
        try:
            profile_response = model.generate_content(profile_prompt)
            json_text = profile_response.text.strip()

            # Clean JSON response before parsing
            cleaned_json_text = clean_json_response(json_text)

            # Parse JSON after cleaning
            json_output = json.loads(cleaned_json_text)
            break  # Success, exit retry loop

        except json.JSONDecodeError:
            print(f" Invalid JSON response, retrying... (Attempt {attempt+1}/{retry_attempts})")
            time.sleep(5)

    # Return empty JSON if all retries fail
    if not json_output:
        json_output = {"labels": []}

    return json_output


# ============================
# Main Execution
# ============================
def main():
    process_files()
    extracted_text = extract_text_from_images()

    google_form_url = input("\nEnter Google Form URL to extract labels (or press Enter to skip): ")
    if google_form_url:
        extracted_text += f"\n--- Google Form Labels ---\n{extract_labels_from_web_form(google_form_url)}\n\n"

    json_data = generate_json_profile(extracted_text)

    output_file = "Extracted_Data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)

    print(f" Extracted data saved to {output_file}")

if __name__ == "__main__":
    main()
