import camelot

# Extract tables from the PDF
tables = camelot.read_pdf("file:///D:/ledgerdaddy/statement.pdf", flavor="stream")
print(tables[1].df)
