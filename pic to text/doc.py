from docx import Document

# Load the .docx file
doc = "demo.docx"
doc = Document(doc)

# Extract and print the text from the document
for paragraph in doc.paragraphs:
    print(paragraph.text)
