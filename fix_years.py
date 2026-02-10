import os
import time
from tqdm import tqdm
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb

# --- CONFIGURATION ---
CHROMA_DB_DIR = "./chroma_db_arxiv"
COLLECTION_NAME = "arxiv"
BATCH_SIZE = 5000  # Process 5k papers at a time

def main():
    print(f"Connecting to DB at {CHROMA_DB_DIR}...")
    
    # 1. Direct Client Connection (Bypassing LangChain for raw access)
    # We use the native chromadb client for easier metadata manipulation
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"Error: Could not find collection '{COLLECTION_NAME}'. {e}")
        return

    total_count = collection.count()
    print(f"Found {total_count} documents. Starting update process...")

    # 2. Iterate and Update
    # We use offset-based pagination to process in chunks
    for offset in tqdm(range(0, total_count, BATCH_SIZE), desc="Updating Metadata"):
        
        # Fetch a batch of existing data (IDs and Metadata only)
        # We generally don't need embeddings or documents to update metadata
        batch = collection.get(
            limit=BATCH_SIZE, 
            offset=offset, 
            include=["metadatas"] 
        )
        
        ids_to_update = []
        new_metadatas = []
        
        for i, doc_id in enumerate(batch['ids']):
            current_meta = batch['metadatas'][i]
            
            # CHECK: Does 'year' need fixing?
            year_val = current_meta.get("year", "0")
            
            # If it's already an integer, skip logic (but we might need to re-upload if doing bulk)
            # If it's a string, convert it.
            if isinstance(year_val, str):
                try:
                    # Convert "2008" (str) -> 2008 (int)
                    current_meta["year"] = int(year_val)
                    
                    ids_to_update.append(doc_id)
                    new_metadatas.append(current_meta)
                except ValueError:
                    # Handle cases where year might be empty or invalid
                    current_meta["year"] = 0
                    ids_to_update.append(doc_id)
                    new_metadatas.append(current_meta)
            
        # 3. Push Updates to DB
        if ids_to_update:
            collection.update(
                ids=ids_to_update,
                metadatas=new_metadatas
            )

    print("\n--- Update Complete ---")
    print("All 'year' fields are now Integers.")
    print("You can now use '$lte' and '$gte' filters in your search app!")

if __name__ == "__main__":
    main()