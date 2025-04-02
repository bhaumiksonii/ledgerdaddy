import pdfplumber
import re

def extract_bank_statement(pdf_path):
    extracted_data = []
    current_entry = None
    start_extracting = False 

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text_lines = page.extract_text().split("\n")
            
            for line in text_lines:
                
                # Start processing only after "Closing Balance" appears
                if "ClosingBalance" in line:
                    start_extracting = True
                    continue  # Skip this line, move to the next
                if "HDFCBANKLIMITED" in line:
                    start_extracting = False
                if not start_extracting:
                    continue  # Ignore lines before "Closing Balance"

                # ✅ Find all dates in the line
                dates = re.findall(r"\b\d{2}/\d{2}/\d{2}\b", line)

                # ✅ Ensure the line contains **exactly two dates**
                if len(dates) == 2:
                    # Save the previous entry before starting a new one
                    if current_entry:
                        extracted_data.append(current_entry)

                    parts = line.split()
                    transaction_date, posting_date = dates  # Assign detected dates

                    # Extract amount (should be before posting_date)
                    amount = ""
                    for i in range(len(parts) - 2, 0, -1):
                        if re.match(r"[\d,]+\.\d{2}", parts[i]):  # Look for a valid amount format
                            amount = parts[i]
                            description = " ".join(parts[1:i])  # Everything between Date and Amount
                            break
                    else:
                        description = " ".join(parts[1:])  # If no amount is found, assume all is description

                    # Create a new row entry
                    current_entry = [transaction_date, description, amount, posting_date]

                else:
                    # If no two dates, assume it's part of the previous row's description
                    if current_entry:
                        current_entry[1] += " " + line.strip()  # Append to description column
            break
        if current_entry:
            extracted_data.append(current_entry)
    for row in extracted_data:
        print(row)

extract_bank_statement("statement.pdf")
