import os
import glob
import time
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
# API key (Replace with your own)
# ============================
API_KEY = "AIzaSyBmuqdZc1uBK5TQHS323JVcVCuM-0Y48e0"
genai.configure(api_key=API_KEY)

# Initialize the Gemini model (Flash 2.0)
model = genai.GenerativeModel("gemini-2.0-flash")

# ============================
# Directory user input
# ============================
root = tk.Tk()
root.withdraw()  # Hide the main window
print("Select the folder containing the files")
INPUT_FOLDER = filedialog.askdirectory(title="Select the folder containing the files")
if not INPUT_FOLDER:
    print("No folder selected. Exiting.")
    exit(1)

# File to store all extracted output
output_file = os.path.join(INPUT_FOLDER, "extracted_labels.txt")

# ============================
# Supported File Types
# ============================
image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
docx_exts  = {".docx"}
txt_exts   = {".txt"}
pdf_exts   = {".pdf"}

# ============================
# Poppler Path
# ============================
poppler_path = r"C:\poppler\poppler-24.08.0\Library\bin"
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
        os.remove(pdf_path)  # Cleanup intermediate PDF
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
        pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        pdf.set_font("DejaVu", "", 12)
        with open(txt_path, "r", encoding="utf-8-sig") as file:
            for line in file:
                pdf.multi_cell(0, 10, line)
        pdf.output(pdf_path)
        convert_pdf_to_images(pdf_path)
        os.remove(pdf_path)  # Cleanup intermediate PDF
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
        elif ext in image_exts:
            continue  # Already an image
        else:
            print(f"Skipping unsupported file type: {file_path}")

# ============================
# Extract Labels from Images
# ============================
def extract_labels_from_images(output_file):
    all_files = glob.glob(os.path.join(INPUT_FOLDER, "*"))
    with open(output_file, "a", encoding="utf-8") as f:
        for file_path in all_files:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in image_exts:
                try:
                    img = Image.open(file_path)
                except Exception as e:
                    print(f"Error opening image {file_path}: {e}")
                    continue

                label_prompt = (
                    "Extract only the labels (field names) from this form. "
                    "Do not include any values. Return only the labels. "
                    "If multiple labels are repeated, reference them as 'Name 1', 'Name 2', etc."
                )
                
                try:
                    response = model.generate_content([label_prompt, img])
                    labels = response.text.strip()
                except Exception as e:
                    print(f"Error extracting labels from image {file_path}: {e}")
                    continue
                
                img.close()
                time.sleep(15)  # Avoid rate limiting
                
                f.write(f"[START OF FORM] {os.path.basename(file_path)}\n")
                f.write(labels + "\n")
                f.write("[END OF FORM]\n\n")

# ============================
# Extract Labels from Web Form
# ============================
def extract_labels_from_web_form(url, output_file):
    options = Options()
    options.headless = False  
    options.add_argument("--disable-blink-features=AutomationControlled")  
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")  
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        time.sleep(40)  
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.TAG_NAME, 'form')))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        questions = soup.select('div[role="heading"]')

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"[START OF FORM] {url}\n")
            for i, question in enumerate(questions, 1):
                label = question.get_text(strip=True)
                f.write(f"Q{i}: {label}\n")
            f.write("[END OF FORM]\n\n")
    except Exception as e:
        print(f"❌ Error extracting from web form: {e}")
    finally:
        driver.quit()

# ============================
# Main Execution
# ============================
def main():
    process_files()
    extract_labels_from_images(output_file)

    google_form_url = input("\nEnter Google Form URL to extract labels (or press Enter to skip): ")
    if google_form_url:
        extract_labels_from_web_form(google_form_url, output_file)

    for image_path in converted_images:
        try:
            os.remove(image_path)
        except Exception as e:
            print(f"Error deleting {image_path}: {e}")

if __name__ == "__main__":
    main()
