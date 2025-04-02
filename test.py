import re
import pandas as pd
import numpy as np
from PyPDF2 import PdfReader
from io import StringIO
import pdfplumber  # Better tool for spatial analysis of PDF content

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_tables_with_pdfplumber(pdf_path):
    """Extract tables from PDF using pdfplumber which handles borderless tables better."""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract tables with explicit and implicit borders
            # For borderless tables, we need to define table settings
            table_settings = {
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
                "min_words_vertical": 2,
                "min_words_horizontal": 1,
                "snap_tolerance": 5,
                "intersection_tolerance": 3,
                "edge_min_length": 3,
                "text_tolerance": 3,
                "join_tolerance": 3,
            }
            
            # Try to extract tables with the settings
            page_tables = page.extract_tables(table_settings)
            if page_tables:
                tables.extend(page_tables)
            
            # If no tables found, try to extract all text and analyze its structure
            if not page_tables:
                words = page.extract_words()
                if words:
                    # Group words by their vertical position (approximating rows)
                    y_positions = {}
                    for word in words:
                        y_key = round(word['top'] / 10) * 10  # Round to nearest 10 for grouping
                        if y_key not in y_positions:
                            y_positions[y_key] = []
                        y_positions[y_key].append(word)
                    
                    # Sort words in each row by horizontal position
                    for y_key in y_positions:
                        y_positions[y_key].sort(key=lambda w: w['x0'])
                    
                    # Convert to a table format
                    sorted_y_keys = sorted(y_positions.keys())
                    text_table = []
                    for y_key in sorted_y_keys:
                        row = ' '.join([w['text'] for w in y_positions[y_key]])
                        text_table.append([row])
                    
                    tables.append(text_table)
    
    return tables

def parse_bank_statement(pdf_path):
    """Parse bank statement PDF and extract transaction data."""
    # Try first with pdfplumber for better table extraction
    tables = extract_tables_with_pdfplumber(pdf_path)
    
    # If pdfplumber found tables, process them
    if tables and any(table for table in tables if len(table) > 1):
        return process_extracted_tables(tables, pdf_path)
    
    # Fallback to text-based extraction
    text = extract_text_from_pdf(pdf_path)
    return parse_bank_statement_from_text(text)

def process_extracted_tables(tables, pdf_path):
    """Process tables extracted by pdfplumber."""
    # Identify the transaction table
    transaction_table = None
    for table in tables:
        # Look for tables with date patterns or header rows that look like transaction data
        if any(cell and isinstance(cell, str) and re.search(r'\d{2}/\d{2}/\d{2}', cell) for row in table for cell in row):
            transaction_table = table
            break
    
    if not transaction_table:
        print("No transaction table found. Falling back to text extraction.")
        return parse_bank_statement_from_text(extract_text_from_pdf(pdf_path))
    
    # Clean and process the transaction table
    # Remove empty rows and columns
    cleaned_table = []
    for row in transaction_table:
        if row and any(cell for cell in row):
            # Remove empty cells and strip whitespace
            cleaned_row = [str(cell).strip() if cell else "" for cell in row]
            cleaned_table.append(cleaned_row)
    
    # Determine if the first row is a header row
    header_row = None
    for i, row in enumerate(cleaned_table):
        if any(header in ' '.join(row).upper() for header in ["DATE", "NARRATION", "AMOUNT", "BALANCE"]):
            header_row = i
            break
    
    # If header row found, use it; otherwise infer columns
    if header_row is not None:
        headers = cleaned_table[header_row]
        data_rows = cleaned_table[header_row+1:]
    else:
        # Infer headers based on typical bank statement columns
        date_col = -1
        for i, row in enumerate(cleaned_table):
            for j, cell in enumerate(row):
                if re.search(r'\d{2}/\d{2}/\d{2}', cell):
                    date_col = j
                    break
            if date_col >= 0:
                break
        
        if date_col >= 0:
            # Assume a basic structure with date followed by description and amounts
            headers = ["Date", "Narration", "Chq./Ref.No.", "Value Dt", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"]
            data_rows = [row for row in cleaned_table if any(re.search(r'\d{2}/\d{2}/\d{2}', cell) for cell in row)]
        else:
            print("Could not determine table structure.")
            return None, None, None, None
    
    # Process transactions with awareness of multiline entries
    transactions = []
    current_transaction = None
    
    for row in data_rows:
        # Check if this row starts a new transaction (contains a date)
        has_date = any(re.search(r'\d{2}/\d{2}/\d{2}', cell) for cell in row)
        
        if has_date:
            # Add previous transaction if exists
            if current_transaction:
                transactions.append(current_transaction)
            
            # Start a new transaction
            # Map row data to appropriate columns
            current_transaction = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    current_transaction[header] = row[i]
                else:
                    current_transaction[header] = ""
        elif current_transaction:
            # This is a continuation of the previous transaction
            # Usually these are continuations of the narration
            narration_ext = " ".join(cell for cell in row if cell)
            if "Narration" in current_transaction:
                current_transaction["Narration"] += " " + narration_ext
    
    # Add the last transaction
    if current_transaction:
        transactions.append(current_transaction)
    
    # Extract account information from PDF text
    text = extract_text_from_pdf(pdf_path)
    account_match = re.search(r'Account No\s*:\s*(\d+)', text)
    account_number = account_match.group(1) if account_match else "Unknown"
    
    date_range_match = re.search(r'From\s*:\s*(\d{2}/\d{2}/\d{4})\s*To\s*:\s*(\d{2}/\d{2}/\d{4})', text)
    date_range = f"{date_range_match.group(1)} to {date_range_match.group(2)}" if date_range_match else "Unknown"
    
    # Extract summary
    summary_match = re.search(r'Opening Balance\s+Dr Count\s+Cr Count\s+Debits\s+Credits\s+Closing Bal\s+([0-9,.]+)\s+(\d+)\s+(\d+)\s+([0-9,.]+)\s+([0-9,.]+)\s+([0-9,.]+)', text)
    
    if summary_match:
        summary = {
            "Opening Balance": summary_match.group(1),
            "Debit Count": summary_match.group(2),
            "Credit Count": summary_match.group(3),
            "Total Debits": summary_match.group(4),
            "Total Credits": summary_match.group(5),
            "Closing Balance": summary_match.group(6)
        }
    else:
        summary = None
    
    # Create DataFrame
    df = pd.DataFrame(transactions)
    
    return df, account_number, date_range, summary

def parse_bank_statement_from_text(text):
    """Fallback method to parse bank statement from extracted text."""
    # This is the original text-based parsing logic
    # Extract account details
    account_match = re.search(r'Account No\s*:\s*(\d+)', text)
    account_number = account_match.group(1) if account_match else "Unknown"
    
    date_range_match = re.search(r'From\s*:\s*(\d{2}/\d{2}/\d{4})\s*To\s*:\s*(\d{2}/\d{2}/\d{4})', text)
    date_range = f"{date_range_match.group(1)} to {date_range_match.group(2)}" if date_range_match else "Unknown"
    
    # Find the start of transaction data
    headers = ["Date", "Narration", "Chq./Ref.No.", "Value Dt", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"]
    
    # Split text into lines
    lines = text.split('\n')
    
    # Find where transactions begin
    transaction_start = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("Date") and "Narration" in line and "Closing Balance" in line:
            transaction_start = i + 1
            break
    
    if transaction_start == -1:
        return None, None, None, None
    
    # Extract transaction data
    transactions = []
    current_transaction = None
    
    for line in lines[transaction_start:]:
        # Skip empty lines
        if not line.strip():
            continue
            
        # Check if line starts with date pattern (DD/MM/YY)
        date_match = re.match(r'(\d{2}/\d{2}/\d{2})\s', line)
        
        if date_match:
            # If there's a current transaction, add it to the list
            if current_transaction:
                transactions.append(current_transaction)
            
            # Extract data using regex
            # This regex tries to capture the pattern of transactions in the PDF
            transaction_match = re.search(
                r'(\d{2}/\d{2}/\d{2})\s+(.*?)\s+([A-Z0-9]+\d{2,})\s+(\d{2}/\d{2}/\d{2})\s+(\d{1,3}(?:,\d{3})*\.\d{2})?\s+(\d{1,3}(?:,\d{3})*\.\d{2})?\s+(\d{1,3}(?:,\d{3})*\.\d{2})',
                line
            )
            
            if transaction_match:
                date = transaction_match.group(1)
                narration = transaction_match.group(2).strip()
                ref_no = transaction_match.group(3)
                value_dt = transaction_match.group(4)
                withdrawal = transaction_match.group(5) or ""
                deposit = transaction_match.group(6) or ""
                closing_balance = transaction_match.group(7)
                
                current_transaction = {
                    "Date": date,
                    "Narration": narration,
                    "Chq./Ref.No.": ref_no,
                    "Value Dt": value_dt,
                    "Withdrawal Amt.": withdrawal,
                    "Deposit Amt.": deposit,
                    "Closing Balance": closing_balance
                }
            else:
                # If regex doesn't match but line starts with date, try to extract data by position
                parts = line.split()
                if len(parts) >= 5:
                    date = parts[0]
                    # Complex logic to determine which parts are which
                    closing_balance = parts[-1]
                    
                    # Check if second-to-last part is a number with commas and decimals
                    if re.match(r'\d{1,3}(?:,\d{3})*\.\d{2}', parts[-2]):
                        if re.match(r'\d{1,3}(?:,\d{3})*\.\d{2}', parts[-3]):
                            # Both withdrawal and deposit are present
                            deposit = parts[-2]
                            withdrawal = parts[-3]
                            ref_no = parts[-4]
                            value_dt = parts[-5]
                            narration = ' '.join(parts[1:-5])
                        else:
                            # Only one of withdrawal or deposit is present
                            amount = parts[-2]
                            ref_no = parts[-3]
                            value_dt = parts[-4]
                            narration = ' '.join(parts[1:-4])
                            
                            # Determine if it's withdrawal or deposit based on narration
                            if "DR-" in narration or "BILLPA" in narration:
                                withdrawal = amount
                                deposit = ""
                            else:
                                withdrawal = ""
                                deposit = amount
                    else:
                        # Unusual format, try best effort parsing
                        narration = ' '.join(parts[1:])
                        ref_no = ""
                        value_dt = ""
                        withdrawal = ""
                        deposit = ""
                    
                    current_transaction = {
                        "Date": date,
                        "Narration": narration,
                        "Chq./Ref.No.": ref_no,
                        "Value Dt": value_dt,
                        "Withdrawal Amt.": withdrawal,
                        "Deposit Amt.": deposit,
                        "Closing Balance": closing_balance
                    }
        elif "STATEMENT SUMMARY" in line:
            # We've reached the end of transactions
            if current_transaction:
                transactions.append(current_transaction)
            break
        elif current_transaction:
            # This line is a continuation of the narration for the current transaction
            current_transaction["Narration"] += " " + line.strip()
    
    # Add the last transaction if there is one
    if current_transaction and current_transaction not in transactions:
        transactions.append(current_transaction)
    
    # Extract summary information
    summary_match = re.search(r'Opening Balance\s+Dr Count\s+Cr Count\s+Debits\s+Credits\s+Closing Bal\s+([0-9,.]+)\s+(\d+)\s+(\d+)\s+([0-9,.]+)\s+([0-9,.]+)\s+([0-9,.]+)', text)
    
    if summary_match:
        summary = {
            "Opening Balance": summary_match.group(1),
            "Debit Count": summary_match.group(2),
            "Credit Count": summary_match.group(3),
            "Total Debits": summary_match.group(4),
            "Total Credits": summary_match.group(5),
            "Closing Balance": summary_match.group(6)
        }
    else:
        summary = None
    
    # Create DataFrame
    df = pd.DataFrame(transactions)
    
    return df, account_number, date_range, summary

def clean_transaction_data(df):
    """Clean and format the transaction data."""
    if df is None or df.empty:
        return None
    
    # Remove any duplicated rows
    df = df.drop_duplic