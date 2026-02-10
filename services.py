import os
from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq

chroma_db_path = "./chroma_db_arxiv"
collection_name = "arxiv"

print("Initializing modules...")

load_dotenv()

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = Chroma(
    collection_name=collection_name,
    embedding_function=embeddings,
    persist_directory=chroma_db_path
)

groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=SecretStr(groq_api_key) if groq_api_key is not None else None
)

# TODO: this + citations
# reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

print("Modules initialized.")