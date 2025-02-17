import streamlit as st
import requests

FASTAPI_URL = "http://fastapi-container:8080"

if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = set()  

st.title("Upload multiple PDFs & Ask a question")

# Khu vực upload file
uploaded_files = st.file_uploader("Upload PDF(s)", 
                                  type=["pdf"], 
                                  accept_multiple_files=True)

# Nút upload riêng
if st.button("Upload file(s)"):
    if uploaded_files:
        with st.spinner("Uploading..."):
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in st.session_state["uploaded_files"]:
                    files = {
                        "pdf": (uploaded_file.name, uploaded_file, "application/pdf")
                    }
                    response = requests.post(f"{FASTAPI_URL}/upload/", files=files)
                    
                    if response.status_code == 200:
                        st.success(f"Uploaded {uploaded_file.name} to Qdrant successfully!")
                        st.session_state["uploaded_files"].add(uploaded_file.name)
                    else:
                        st.error(f"Failed to upload {uploaded_file.name}")
    else:
        st.warning("Please choose at least one PDF file.")

# Query input for RAG flow
question = st.text_input("Ask a question:")

if st.button("Submit"):
    if question:
        payload = {"question": question}

        with st.spinner("Thinking..."):
            response = requests.post(f"{FASTAPI_URL}/rag_flow/", json=payload)

        if response.status_code == 200:
            st.write("Answer:", response.json().get("answer"))
        else:
            st.error("Failed to get an answer.")
