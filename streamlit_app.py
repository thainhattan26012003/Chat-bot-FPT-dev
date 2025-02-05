# streamlit_app.py
import streamlit as st
import requests

FASTAPI_URL = "http://fastapi-container:8080"


# File upload widget
uploaded_file = st.file_uploader("Upload an Image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    files = {"image": (uploaded_file.name, uploaded_file, "application/octet-stream")}
    response = requests.post(f"{FASTAPI_URL}/upload/", files=files)
    
    if response.status_code == 200:
        st.success("Text uploaded to Qdrant successfully!")
    else:
        st.error(f"Failed to upload: {response.json()['message']}")

# Query input for RAG flow
question = st.text_input("Ask a question:")

if question:
    payload = {"question": question}
    response = requests.post(f"{FASTAPI_URL}/rag_flow/", json=payload)
    
    if response.status_code == 200:
        st.write("Answer:", response.json().get("answer"))
    else:
        st.error("Failed to get an answer.")
