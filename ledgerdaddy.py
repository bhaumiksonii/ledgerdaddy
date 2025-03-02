import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import pdfplumber  # Extract tables from PDFs
import random

# Streamlit App Title
st.title("LedgerDaddy!!")

# User input for name
name = st.text_input("Enter your Name:")

# File uploader for PDF
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
def convert_money(value):
    if pd.isna(value):
        return 0  # Return 0 for NaN values
    value = str(value).replace(",", "").strip()  # Remove commas
    if "Cr" in value:
        return float(value.replace("Cr", "")) * 10**7  # Convert Crore to numeric
    elif "Lakh" in value:
        return float(value.replace("Lakh", "")) * 10**5  # Convert Lakh to numeric
    else:
        try:
            return float(value)  # Convert normal numbers
        except ValueError:
            return 0
if uploaded_file:
    # Ask for PDF password
    password = st.text_input("Enter PDF Password (if required)", type="password")

    # Process PDF
    try:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        if doc.needs_pass:
            if not doc.authenticate(password):
                st.error("Incorrect password! ❌")
                st.stop()
            else:
                st.success("Correct password!")

        tables = []
        with pdfplumber.open(uploaded_file, password=password) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    tables.append(pd.DataFrame(table))

        if not tables:
            st.warning("No tables found in the PDF!")
        else:
            # Combine tables into a single DataFrame
            df = pd.concat(tables, ignore_index=True)
            print("dfasda",df)
            # Use the first row as headers
            df.columns = df.iloc[0]
            df = df[1:].reset_index(drop=True)

            # Filter based on user name
            if name:
                filtered_df = df[df["Particulars"].str.contains(name, case=False, na=False)]
                st.write(f"🔍 Showing results for **{name}**:")
                # filtered_df["Balance(INR)"] = filtered_df["Balance(INR)"].apply(convert_money)

                # Calculate Total Money
                # total_money = filtered_df["Withdrawla"].sum()
                # print("qonowdhqow",filtered_df["Balance(INR)"])
                # total_money = filtered_df["Balance(INR)"].sum()
                # st.subheader(f"💰 Total Money: **₹{total_money:,.2f}**")
                filtered_df = filtered_df.drop("Balance(INR)") 
                st.dataframe(filtered_df, use_container_width=True,width=400)

            else:
                st.warning("Please enter your name to filter the table.")

    except Exception as e:
        st.error(f"Error processing PDF: {e}")

else:
    st.info("Please upload a PDF file to continue.")

