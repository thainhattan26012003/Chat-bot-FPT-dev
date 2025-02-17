import os
import torch
import uuid
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client.http import models
from qdrant_client.models import PointStruct
from qdrant_client import QdrantClient

load_dotenv('.env')

device = "cuda" if torch.cuda.is_available() else "cpu"

client = QdrantClient(url=os.getenv("QDRANT_URL"), 
    api_key=os.getenv("QDRANT_API_KEY"))

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", trust_remote_code=True, device=device)

def embed(chunk):
    embedding = model.encode(chunk, convert_to_numpy=True, device=device)
    return embedding.tolist()

DEFAULT_DISTANCE = "cosine"

class QdrantProvider:
    def __init__(self):
        # Initialize the QdrantProvider with a specific collection name
        self.vector_size = model.get_sentence_embedding_dimension()  
        self.distance = DEFAULT_DISTANCE

    def create_collection(self, collection_name: str):
        # Check if the collection already exists
        if collection_name in self.list_collections():
            print(f"Collection `{collection_name}` already exists.")
            return

        # Create a new collection with the specified vector size and distance metric
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance[self.distance.upper()]
            )
        )
        print(f"Collection created `{collection_name}`")
        
    def list_collections(self):
        # List all existing collections in the Qdrant database
        collections = client.get_collections()
        return [col.name for col in collections.collections]
        
    def add_vectors_(self, collection_name: str, text):
        """Add multiple vectors to the client collection."""
        points = []

        for i, chunk in enumerate(text):
            vector = embed(chunk)
            
            point = PointStruct(
                id=str(uuid.uuid4()),  
                vector=vector,  
                payload={
                    "content": chunk, 
                }
            )
            points.append(point)
        client.upsert(collection_name=collection_name, points=points)
        print(f"{len(points)} Vectors added to `{collection_name}`")

    def search_vector(self, collection_name: str, vector: list[float], limit=3, with_payload=True):
        # Perform the search query in client with the provided parameters
        search_result = client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit,  # Limit the number of search results
            with_payload=with_payload,  # Whether to include payload in results
        )
        print(f"Vector searched `{collection_name}`")
        return search_result

        
