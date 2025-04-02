import camelot

# Extract tables from the PDF
tables = camelot.read_pdf("file:///C:/Users/Bhaumik/Downloads/canara_epassbook_2025-03-05%2013_47_42.315041.pdf", flavor="stream")
print(tables[1].df)
