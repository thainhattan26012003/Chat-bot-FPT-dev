import os 
import io
import requests
import tempfile
import openai
import numpy as np 
import cv2 as cv
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from vector_db import embed, QdrantProvider
from dotenv import load_dotenv

load_dotenv()


app = FastAPI()

text_splitter = RecursiveCharacterTextSplitter(

    chunk_size=1024,
    chunk_overlap=200,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

qdrant_name = 'CHATBOT_FPT_AI'
vectordb_provider = QdrantProvider()
vectordb_provider.create_collection(qdrant_name)

EXTRACT_TEXTS_URL = "http://ec2-52-1-115-193.compute-1.amazonaws.com:8000/extract_texts"
    
@app.post("/upload/")
async def upload_file(pdf: UploadFile = File(...)):
    try:
        pdf_bytes = pdf.file.read()
        
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        for page_index in range(len(doc)):
            page = doc[page_index]
            images = page.get_images(full=True)
            
            for img_idx, img in enumerate(images):
                xref = img[0]  # Get the image reference number
                
                base_image = doc.extract_image(xref)  # Extract the image
                image_bytes = base_image["image"]  # Get the image bytes
                image_ext = base_image["ext"]  # Get the image extension (e.g., 'png', 'jpeg')

                image_filename = f"page_{page_index}_img_{img_idx}.{image_ext}"
                
                # Load numpy array
                image_array = cv.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv.IMREAD_COLOR)

                # Rotate 90 degree
                image_array = cv.rotate(image_array, cv.ROTATE_90_COUNTERCLOCKWISE)
                
                success, encoded_image = cv.imencode(".jpg", image_array)
                if not success:
                    continue
                jpeg_bytes = encoded_image.tobytes()

                files = {"image": (image_filename, jpeg_bytes, "image/jpeg")}
                
                response = requests.post(EXTRACT_TEXTS_URL, files=files)

                if response.status_code == 200:

                    split_text = text_splitter.split_text(response.json().get("data"))
                
                    vectordb_provider.add_vectors_(qdrant_name, split_text)
                    
                    print ({"status": "success", "message": "Text uploaded to Qdrant"})
                else:
                    print ({"status": response.status_code, "message": "Failed to extract text from image"})
        return JSONResponse(
            status_code=200,
            content={"Message:":"All page image have been extracted and uploaded to Qdrant!"} 
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class Question(BaseModel):
    question: str

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_answer_from_llm(query: str, context: str):
    prompt = f"Question: {query}\nContext: {context}\nAnswer:"
    
    response = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a well-done assistant. Answer only based on knowledge from database. NO FLUFF. DO NOT RETURN THE ANSWER IF YOU DO NOT KNOW!"},
        {"role": "user", "content": prompt}
    ],
    max_tokens=200
)

    return response["choices"][0]["message"]["content"].strip()

@app.post("/rag_flow/")
async def rag_flow(question: Question):
    search_results = vectordb_provider.search_vector(qdrant_name, embed(question.question))
    context = " ".join([result.payload["content"] for result in search_results])
    
    answer = generate_answer_from_llm(question.question, context)

    return JSONResponse(
        status_code=200,
        content={"answer": answer}
    )


