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

pdf_path = "P:\FA24\extract_texts\\test_data\documents.pdf"

def extract_all_pages_images(file_upload):
    pdf_pages = []
    
    with pdfplumber.open(file_upload) as pdf:
        pdf_pages = [page.to_image().original for page in pdf.pages]
        
        return pdf_pages

FASTAPI_URL = "http://fastapi-container:8080"

st.set_page_config(page_title="Demo AI Extract Documents App", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")

col1, col2 = st.columns([1.5, 2])

# Query input for RAG flow
question = col1.text_input("Ask a question:")

with col1:
    if st.button("Submit"):
        if question:
            payload = {"question": question}

            with st.spinner("Thinking..."):
                response = requests.post(f"{FASTAPI_URL}/rag_flow/", json=payload)

            if response.status_code == 200:
                st.write("Answer:", response.json().get("answer"))
            else:
                st.error("Failed to get an answer.")

with col2:
    st.write("### Nội dung file PDF:")

    pdf_pages = extract_all_pages_images(pdf_path)
    
    st.session_state["pdf_pages"] = pdf_pages
    
    zoom_level = col2.slider("Zoom level", min_value=100, max_value=1000, value=700, step=100)
    
    with st.container(height=800, border=True):
        for page in pdf_pages:
            st.image(page, use_container_width=True, output_format="PNG", width=zoom_level)
