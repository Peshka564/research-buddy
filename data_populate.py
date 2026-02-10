import json
import os
import time
from typing import Generator
from itertools import islice

from tqdm import tqdm
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# https://www.kaggle.com/datasets/Cornell-University/arxiv
paper_metadata_path = "./arxiv-metadata-oai-snapshot.json"
chromadb_path = "./chroma_db_arxiv"
collection_name = "arxiv"
batch_size = 500

print("Loading Embedding Model...")
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = Chroma(
    collection_name=collection_name,
    embedding_function=embedding_function,
    persist_directory=chromadb_path
)

def process_metadata(paper: dict) -> dict:
    """Clean and select only necessary metadata fields to save space."""
    return {
        "id": paper.get("id", ""),
        "authors": paper.get("authors", "")[:200],
        "categories": paper.get("categories", ""),
        # "doi": paper.get("doi") or "",

        # Extract year from YYYY-MM-DD
        "year": paper.get("update_date", "")[:4]
    }

def arxiv_generator(file_path: str) -> Generator[dict, None, None]:
    """Yields parsed JSON objects one by one from the metadata file."""
    with open(file_path, 'r') as f:
        # The first 77k docs are already inserted
        line_iterator = islice(f, 111500, None)
        for line in line_iterator:
            if not line.strip(): continue
            yield json.loads(line)

def batch_loader(iterator, batch_size):
    batch = []
    for item in iterator:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

def main():
    if not os.path.exists(paper_metadata_path):
        print(f"Error: File {paper_metadata_path} not found.")
        return

    print(f"Starting population of data...")
    
    paper_stream = arxiv_generator(paper_metadata_path)
    
    start_time = time.time()
    count = 0
    
    try:
        for batch in tqdm(batch_loader(paper_stream, batch_size), desc="Inserting Batches"):
            documents = []
            
            for paper in batch:
                # if int(paper.get("update_date", "0000")[:4]) < 2020: continue

                content = f"Title: {paper['title']}\n" \
                          f"Categories: {paper['categories']}\n" \
                          f"Abstract: {paper['abstract']}"
                
                doc = Document(
                    page_content=content,
                    metadata=process_metadata(paper)
                )
                documents.append(doc)
            
            if documents:
                vector_store.add_documents(documents)
                count += len(documents)

            # if count >= 5000:
            #    print("Reached limit of 5000 papers. Stopping for test.")
            #    break

    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Saving progress...")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Total Papers Embedded: {count}")
    print(f"Time Taken: {duration:.2f} seconds")

if __name__ == "__main__":
    main()