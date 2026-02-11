import os
from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_chroma import Chroma
from langchain_groq import ChatGroq

chroma_db_path = "./chroma_db_arxiv"

print("Initializing modules...")

load_dotenv()

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

metadata_vector_store = Chroma(
    collection_name="arxiv",
    embedding_function=embeddings,
    persist_directory=chroma_db_path
)

groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=SecretStr(groq_api_key) if groq_api_key is not None else None
)

vlm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct", 
    api_key=SecretStr(groq_api_key) if groq_api_key is not None else None,
    temperature=0.1
)

# TODO: citations
reranker = HuggingFaceCrossEncoder(model_name='cross-encoder/ms-marco-MiniLM-L-6-v2')

print("Modules initialized.")