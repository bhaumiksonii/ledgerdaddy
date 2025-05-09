import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import pdfplumber  # Extract tables from PDFs
import random

# Streamlit App Title
st.title("LedgerDaddy!!!!!")

# User input for name
name = st.text_input("Filter Name:")

# File uploader for PDF
uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    # Ask for PDF password
    password = st.text_input("Enter PDF Password (if required)", type="password")

    all_data = []  # List to store data from all PDFs

    for uploaded_file in uploaded_files:
        try:
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            if doc.needs_pass:
                if not doc.authenticate(password):
                    st.error(f"Incorrect password for {uploaded_file.name}! ❌")
                    continue  # Skip this file
                else:
                    st.success(f"Correct password for {uploaded_file.name}! ✅")

            tables = []
            with pdfplumber.open(uploaded_file, password=password) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table:
                        tables.append(pd.DataFrame(table))

            if tables:
                df = pd.concat(tables, ignore_index=True)
                df.columns = df.iloc[0]  # First row as header
                df = df[1:].reset_index(drop=True)
                all_data.append(df)

        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {e}")

    if all_data:
        # Combine all PDFs data into a single DataFrame
        combined_df = pd.concat(all_data, ignore_index=True)

        # Filter by user name
        if name:
            filtered_df = combined_df[combined_df["Particulars"].str.contains(name, case=False, na=False)]
            st.write(f"🔍 Showing results for **{name}**:")

            # Drop Balance column
            filtered_df = filtered_df.drop("Balance(INR)", axis=1)

            # Convert Withdrawals and Deposits to numeric
            filtered_df[['Withdrawals', 'Deposits']] = filtered_df[['Withdrawals', 'Deposits']].replace({',': ''}, regex=True).astype(float).astype(int)

            # Calculate Grand Total row
            filtered_df= filtered_df.rename(columns={"Reverse\nSweep": "ReverseSweep"})
            print(filtered_df.columns)
            new_row = pd.DataFrame([{col: filtered_df[col].sum() if col in ['Withdrawals', 'Deposits'] else ('Grand Total' if col == 'Chq.No.' else ( "{:,}".format((filtered_df["Withdrawals"].sum() - filtered_df["Deposits"].sum())) if col == 'ReverseSweep' else ('Difference' if col == 'Autosweep' else ""))) for col in filtered_df.columns}])

            # Append Grand Total row
            filtered_df = pd.concat([filtered_df, new_row], ignore_index=True)

            # Display DataFrame
            st.dataframe(filtered_df, use_container_width=True)

        else:
            st.warning("Please enter your name to filter the table.")

    else:
        st.warning("No tables found in any PDFs")

else:
    st.info("Please upload PDF files to continue.")
