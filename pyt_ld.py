import pytesseract
from pdf2image import convert_from_path

# Convert PDF pages to images
images = convert_from_path("statement.pdf")

# Extract text using pytesseract
extracted_text = []
for img in images:
    text = pytesseract.image_to_string(img)
    extracted_text.append(text)

# Combine text from all pages
full_text = "\n".join(extracted_text)

print(full_text)