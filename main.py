import os 
import io
import requests
import tempfile
import openai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from vector_db import embed, QdrantProvider
from pdf2image import convert_from_path
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

qdrant_name = 'test'
vectordb_provider = QdrantProvider()

EXTRACT_TEXTS_URL = "http://ec2-52-1-115-193.compute-1.amazonaws.com:8000/extract_texts"
    
@app.post("/upload/")
async def upload_file(image: UploadFile = File(...)):
    try:
        file_bytes = await image.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(file_bytes)
            tmp_pdf_path = tmp_pdf.name
            
        images = convert_from_path(tmp_pdf_path)
        responses = []
        
        for i, image in enumerate(images, start=1):
            img_buffer = io.BytesIO()
            image.save(img_buffer, format="JPEG")
            img_buffer.seek(0)

        files = {"image": (f"page_{i}.jpeg", img_buffer, "image/jpeg")}
        
        response = requests.post(EXTRACT_TEXTS_URL, files=files)

        if response.status_code == 200:
            
            vectordb_provider.create_collection(qdrant_name)

            split_text = text_splitter.split_text(response.json().get("data"))
        
            vectordb_provider.add_vectors_(qdrant_name, split_text)
            
            return {"status": "success", "message": "Text uploaded to Qdrant"}
        else:
            return {"status": response.status_code, "message": "Failed to extract text from image"}

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
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=100
)

    return response["choices"][0]["message"]["content"].strip()

@app.post("/rag_flow/")
async def rag_flow(question: Question):
    search_results = vectordb_provider.search_vector(qdrant_name, embed(question.question))
    for re in search_results:
        print(re.payload["content"])
        print('-'*100)
    context = " ".join([result.payload["content"] for result in search_results])
    print(context)
    
    answer = generate_answer_from_llm(question.question, context)

    return JSONResponse(
        status_code=200,
        content={"answer": answer}
    )


