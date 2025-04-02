import pdfplumber
import re

def extract_bank_statement(pdf_path):
    extracted_data = []
    current_entry = None
    start_extracting = False  # Flag to start processing after "Closing Balance"

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()  # Extract words with positions
            rows = {}

            for word in words:
                text, x, y = word['text'], word['x0'], word['top']

                # Start extraction only after "Closing Balance"
                if "Closing Balance" in text:
                    start_extracting = True
                    continue

                if not start_extracting:
                    continue

                # Group words by similar y-coordinates (same row)
                row_key = round(y, 1)  # Use rounded 'y' value to group words in the same line
                if row_key not in rows:
                    rows[row_key] = []
                rows[row_key].append((text, x))  # Store text along with x position

            # Sort rows by their y-coordinates
            sorted_rows = sorted(rows.items())

            for y, words in sorted_rows:
                words = sorted(words, key=lambda w: w[1])  # Sort words by x-coordinates (left to right)
                line_text = " ".join([w[0] for w in words])  # Recreate structured line

                # Detect transaction date (DD/MM/YY format)
                date_match = re.match(r"(\d{2}/\d{2}/\d{2})", line_text)

                if date_match:
                    # Save previous entry before starting a new one
                    if current_entry:
                        extracted_data.append(current_entry)

                    parts = line_text.split()
                    transaction_date = parts[0]  # First column (Transaction Date)

                    # Detect last part as the Posting Date (4th column)
                    posting_date = parts[-1] if re.match(r"\d{2}/\d{2}/\d{2}", parts[-1]) else ""

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
                    # If no date, it's a continuation of the previous description
                    if current_entry:
                        current_entry[1] += " " + line_text.strip()  # Append to description column

        # Append the last row after loop
        if current_entry:
            extracted_data.append(current_entry)

    # Print extracted data
    for row in extracted_data:
        print(row)

extract_bank_statement("statement.pdf")
