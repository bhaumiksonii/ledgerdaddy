import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import pdfplumber  # Extract tables from PDFs

# Streamlit App Title
st.title("LedgerDaddy!!!!!")

# Bank selection first
bank_type = st.selectbox("🏦 Select Your Bank:", ["ICICI Bank 🏦", "HDFC Bank 💰", "SBI Bank 🏛️"], index=0)

if bank_type:
    # Sidebar options
    name = st.sidebar.text_input("🔍 Filter Name:")
    uploaded_files = st.sidebar.file_uploader("📂 Upload PDF files", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        password = st.sidebar.text_input("🔑 Enter PDF Password (if required)", type="password")
        all_data = []
        
        for uploaded_file in uploaded_files:
            try:
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                if doc.needs_pass and not doc.authenticate(password):
                    st.error(f"❌ Incorrect password for {uploaded_file.name}!")
                    continue
                
                tables = []
                with pdfplumber.open(uploaded_file, password=password) as pdf:
                    for page in pdf.pages:
                        table = page.extract_table()
                        if table:
                            tables.append(pd.DataFrame(table))
                
                if tables:
                    df = pd.concat(tables, ignore_index=True)
                    df.columns = df.iloc[0]
                    df = df[1:].reset_index(drop=True)
                    
                    # Processing based on bank type
                    if "ICICI Bank" in bank_type:
                        df = df.rename(columns={"Reverse\nSweep": "ReverseSweep"})
                    elif "HDFC Bank" in bank_type:
                        df = df.rename(columns={"Txn Details": "TransactionDetails"})
                    elif "SBI Bank" in bank_type:
                        df = df.rename(columns={"Narration": "Details"})
                    
                    all_data.append(df)
            
            except Exception as e:
                st.error(f"⚠️ Error processing {uploaded_file.name}: {e}")
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            
            if name:
                filtered_df = combined_df[combined_df.iloc[:, 1].str.contains(name, case=False, na=False)]
                st.write(f"🔍 Showing results for **{name}**:")
                
                if "Balance" in filtered_df.columns:
                    filtered_df = filtered_df.drop("Balance", axis=1)
                
                numeric_cols = [col for col in ["Withdrawals", "Deposits"] if col in filtered_df.columns]
                if numeric_cols:
                    filtered_df[numeric_cols] = filtered_df[numeric_cols].replace({',': ''}, regex=True).astype(float).astype(int)
                    
                    new_row = {col: filtered_df[col].sum() if col in numeric_cols else "Grand Total" for col in filtered_df.columns}
                    filtered_df = pd.concat([filtered_df, pd.DataFrame([new_row])], ignore_index=True)
                
                st.dataframe(filtered_df, use_container_width=True)
            else:
                st.warning("⚠️ Please enter your name to filter the table.")
        else:
            st.warning("🚨 No tables found in any PDFs.")
    else:
        st.sidebar.info("📌 Please upload PDF files to continue.")
