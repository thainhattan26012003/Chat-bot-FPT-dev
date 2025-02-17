# import streamlit as st
# import requests

# FASTAPI_URL = "http://fastapi-container:8080"

# if "uploaded_files" not in st.session_state:
#     st.session_state["uploaded_files"] = set()  

# st.title("Upload multiple PDFs & Ask a question")

# uploaded_files = st.file_uploader("Upload PDF(s)", 
#                                   type=["pdf"], 
#                                   accept_multiple_files=True)
# # Upload PDFs to Qdrant
# if st.button("Upload file(s)"):
#     if uploaded_files:
#         with st.spinner("Uploading..."):
#             for uploaded_file in uploaded_files:
#                 if uploaded_file.name not in st.session_state["uploaded_files"]:
#                     files = {
#                         "pdf": (uploaded_file.name, uploaded_file, "application/pdf")
#                     }
#                     response = requests.post(f"{FASTAPI_URL}/upload/", files=files)
                    
#                     if response.status_code == 200:
#                         st.success(f"Uploaded {uploaded_file.name} to Qdrant successfully!")
#                         st.session_state["uploaded_files"].add(uploaded_file.name)
#                     else:
#                         st.error(f"Failed to upload {uploaded_file.name}")
#     else:
#         st.warning("Please choose at least one PDF file.")

# # Query input for RAG flow
# question = st.text_input("Ask a question:")

# if st.button("Submit"):
#     if question:
#         payload = {"question": question}

#         with st.spinner("Thinking..."):
#             response = requests.post(f"{FASTAPI_URL}/rag_flow/", json=payload)

#         if response.status_code == 200:
#             st.write("Answer:", response.json().get("answer"))
#         else:
#             st.error("Failed to get an answer.")


import streamlit as st
import requests
import pdfplumber
from io import BytesIO


def extract_all_pages_images(file_upload, dpi=300):
    pdf_pages = []
    
    with pdfplumber.open(file_upload) as pdf:
        pdf_pages = [page.to_image(resolution=dpi).original for page in pdf.pages]
        
        return pdf_pages

FASTAPI_URL = "http://fastapi-container:8080"

st.set_page_config(page_title="Demo AI Extract Documents App", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")

col1, col2 = st.columns([2, 2])


with col1:
    uploaded_files = st.file_uploader("Upload PDF(s)", 
                                    type=["pdf"], 
                                    accept_multiple_files=True)    
    # Query input for RAG flow
    question = col1.text_input("Ask a question:")
    if st.button("Submit"):
        if question:
            payload = {"question": question}

            with st.spinner("Thinking..."):
                response = requests.post(f"{FASTAPI_URL}/rag_flow/", json=payload)

            if response.status_code == 200:
                st.write("Answer:", response.json().get("answer"))
            else:
                st.error("Failed to get an answer.")
    if uploaded_files:
        st.session_state["uploaded_files"] = uploaded_files

with col2:
    st.write("### PDF Viewer")

    if "uploaded_files" in st.session_state and st.session_state["uploaded_files"]:
        pdf_pages = []
        
        for uploaded_file in st.session_state["uploaded_files"]:
            file_bytes = BytesIO(uploaded_file.read())
            pdf_pages.extend(extract_all_pages_images(file_bytes))
        
        with st.container(height=500, border=True):
            for page in pdf_pages:
                st.image(page, use_container_width=True, output_format="PNG")
