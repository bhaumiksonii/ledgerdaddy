import streamlit as st
from pdf_handler import PDFHandler
from auth import Auth

# Streamlit App Title
st.title("LedgerDaddy!!!!!")

# Google Authentication
auth = Auth()
user_info = auth.authenticate()

if user_info:
    st.sidebar.write(f"Logged in as {user_info['name']}")

    # Bank selection
    bank_type = st.selectbox("🏦 Select Your Bank:", ["ICICI Bank 🏦", "HDFC Bank 💰", "SBI Bank 🏛️"], index=0)

    if bank_type:
        # Sidebar options
        name = st.sidebar.text_input("🔍 Filter Name:")
        uploaded_files = st.sidebar.file_uploader("📂 Upload PDF files", type=["pdf"], accept_multiple_files=True)

        if uploaded_files:
            password = st.sidebar.text_input("🔑 Enter PDF Password (if required)", type="password")
            pdf_handler = PDFHandler(uploaded_files, password)
            all_data = pdf_handler.process_pdfs(bank_type)

            if all_data:
                combined_df = pdf_handler.combine_data(all_data)

                if name:
                    filtered_df = pdf_handler.filter_data(combined_df, name)
                    st.write(f"🔍 Showing results for **{name}**:")
                    st.dataframe(filtered_df, use_container_width=True)
                else:
                    st.warning("⚠️ Please enter your name to filter the table.")
            else:
                st.warning("🚨 No tables found in any PDFs.")
        else:
            st.sidebar.info("📌 Please upload PDF files to continue.")
else:
    st.warning("⚠️ Please log in to proceed.")
