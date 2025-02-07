# streamlit_app.py
import streamlit as st
import requests

FASTAPI_URL = "http://fastapi-container:8080"


# File upload widget
uploaded_file = st.file_uploader("Upload an PDF file", type=["pdf"])

if uploaded_file and "uploaded" not in st.session_state:
    st.write(f"File uploaded: {uploaded_file.name}")
    files = {"pdf": (uploaded_file.name, uploaded_file, "application/pdf")}
    
    with st.spinner("Uploading..."):
      response = requests.post(f"{FASTAPI_URL}/upload/", files=files)
    
    if response.status_code == 200:
        st.success("Text uploaded to Qdrant successfully!")
        st.session_state["uploaded"] = True
    else:
        st.error("Failed to upload")

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
