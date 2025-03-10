import pandas as pd
import fitz  # PyMuPDF
import pdfplumber  # Extract tables from PDFs

class PDFHandler:
    def __init__(self, uploaded_files, password):
        self.uploaded_files = uploaded_files
        self.password = password

    def process_pdfs(self, bank_type):
        all_data = []
        for uploaded_file in self.uploaded_files:
            try:
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                if doc.needs_pass and not doc.authenticate(self.password):
                    raise ValueError(f"Incorrect password for {uploaded_file.name}")
                
                tables = []
                with pdfplumber.open(uploaded_file, password=self.password) as pdf:
                    for page in pdf.pages:
                        table = page.extract_table()
                        if table:
                            tables.append(pd.DataFrame(table))
                
                if tables:
                    df = pd.concat(tables, ignore_index=True)
                    df.columns = df.iloc[0]
                    df = df[1:].reset_index(drop=True)

                    # Process based on bank type
                    if "ICICI Bank" in bank_type:
                        df = df.rename(columns={"Reverse\nSweep": "ReverseSweep"})
                    elif "HDFC Bank" in bank_type:
                        df = df.rename(columns={"Txn Details": "TransactionDetails"})
                    elif "SBI Bank" in bank_type:
                        df = df.rename(columns={"Narration": "Details"})

                    all_data.append(df)

            except Exception as e:
                print(f"Error processing {uploaded_file.name}: {e}")
        return all_data

    def combine_data(self, all_data):
        return pd.concat(all_data, ignore_index=True)

    def filter_data(self, combined_df, name):
        filtered_df = combined_df[combined_df.iloc[:, 1].str.contains(name, case=False, na=False)]
        if "Balance" in filtered_df.columns:
            filtered_df = filtered_df.drop("Balance", axis=1)

        numeric_cols = [col for col in ["Withdrawals", "Deposits"] if col in filtered_df.columns]
        if numeric_cols:
            filtered_df[numeric_cols] = filtered_df[numeric_cols].replace({',': ''}, regex=True).astype(float).astype(int)

            new_row = {col: filtered_df[col].sum() if col in numeric_cols else "Grand Total" for col in filtered_df.columns}
            filtered_df = pd.concat([filtered_df, pd.DataFrame([new_row])], ignore_index=True)
        return filtered_df
