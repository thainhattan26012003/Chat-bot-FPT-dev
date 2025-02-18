import streamlit as st
import requests
import pdfplumber
from pdfminer.pdfparser import PDFSyntaxError
from io import BytesIO

# check if the file is a PDF
def is_probably_pdf(file_bytes: bytes) -> bool:
    return file_bytes.startswith(b"%PDF-")

def extract_all_pages_images(file_bytes, dpi=300):
    """
    Extracts images of all pages from the given PDF bytes using pdfplumber.
    Returns a list of PIL images or an empty list if an error occurs.
    """
    try:
        # Wrap in BytesIO
        file_obj = BytesIO(file_bytes)
        file_obj.seek(0)
        # Attempt to open with pdfplumber
        with pdfplumber.open(file_obj) as pdf:
            pdf_pages = [page.to_image(resolution=dpi).original for page in pdf.pages]
        return pdf_pages
    except PDFSyntaxError:
        # Handle invalid PDF
        st.error("This file is not a valid PDF or is corrupted.")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred while parsing PDF: {e}")
        return []

# Initialize session state
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = {}

FASTAPI_URL = "http://fastapi-container:8080"

st.set_page_config(
    page_title="Demo AI Extract Documents App",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# seperate the layout into two columns
col1, col2 = st.columns([2, 2])

with col1:
    st.subheader("Upload PDF(s)")
    
    # upload multiple PDF files
    uploaded_files = st.file_uploader(
        label="Upload one or more PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )

    if st.button("Upload file(s)"):
        if uploaded_files:
            for uploaded_file in uploaded_files:
                filename = uploaded_file.name
                
                # Make sure we haven't already uploaded this file
                if filename not in st.session_state["uploaded_files"]:
                    file_bytes = uploaded_file.read()
                    
                    # Minimal validation to avoid sending junk to FastAPI
                    if not is_probably_pdf(file_bytes):
                        st.warning(f"'{filename}' does not appear to be a valid PDF.")
                        continue
                    
                    # Attempt to send the file to FastAPI
                    try:
                        files = {
                            "pdf": (filename, BytesIO(file_bytes), "application/pdf")
                        }
                        response = requests.post(f"{FASTAPI_URL}/upload/", files=files)

                        if response.status_code == 200:
                            # On success, store the raw bytes in session_state
                            st.session_state["uploaded_files"][filename] = file_bytes
                            st.success(f"Uploaded '{filename}' to Qdrant successfully!")
                        else:
                            st.error(f"Failed to upload '{filename}' (status code: {response.status_code}).")

                    except Exception as e:
                        st.error(f"An error occurred while uploading '{filename}': {e}")
        else:
            st.warning("Please select at least one PDF file before clicking 'Upload file(s)'.")

    st.subheader("Ask a question:")
    question = st.text_input("Enter your question here")

    # Button to submit question
    if st.button("Submit question"):
        if question.strip():
            payload = {"question": question.strip()}
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(f"{FASTAPI_URL}/rag_flow/", json=payload)
                    if response.status_code == 200:
                        answer = response.json().get("answer", "")
                        st.write("**Answer:**", answer)
                    else:
                        st.error(f"Failed to get an answer (status code: {response.status_code}).")
                except Exception as e:
                    st.error(f"An error occurred while trying to get an answer: {e}")
        else:
            st.warning("Please enter a question before submitting.")

with col2:
    st.subheader("PDF Viewer")
    # If we have uploaded files, let the user select which PDF to view
    if st.session_state["uploaded_files"]:
        pdf_names = list(st.session_state["uploaded_files"].keys())
        selected_pdf = st.selectbox("Select a PDF to view", pdf_names)

        if selected_pdf:
            # Retrieve the raw bytes from session_state
            file_bytes = st.session_state["uploaded_files"][selected_pdf]

            # Extract all page images
            pdf_pages = extract_all_pages_images(file_bytes)

            st.write(f"Showing pages for: **{selected_pdf}**")
            for idx, page_img in enumerate(pdf_pages, start=1):
                st.image(page_img, caption=f"Page {idx}", use_container_width=True)
    else:
        st.info("No PDFs have been uploaded yet. Please upload using the left panel.")
