import tabula

# Extract tables from the PDF
tables = tabula.read_pdf('file:///C:/Users/Bhaumik/Downloads/canara_epassbook_2025-03-05%2013_47_42.315041.pdf', pages=1,password="429601000251")

# Print the number of tables extracted
print(f"Number of tables extracted: {len(tables)}")

# Print the first table
print(tables[0])