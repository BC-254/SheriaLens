import json
import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer


def vector_database(json_filepath, collection_name, db_path="./sherialens_db"):
    print(f"\nLoading data into '{collection_name}'")
    with open(json_filepath, "r", encoding="utf-8") as f:
        knowledge_base = json.load(f)

    client = chromadb.PersistentClient(path=db_path)
    
    # Initializing the Model
    model = SentenceTransformer("BAAI/bge-large-en-v1.5")
       
    collection = client.get_or_create_collection(name=collection_name)
    
    documents = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(knowledge_base):
        documents.append(chunk["text"])
        metadata = {k: str(v) for k, v in chunk.items() if k != "text" and v is not None}
        metadatas.append(metadata)
        
        unique_id = chunk.get("article") or f"{chunk.get('case_name')}_page_{chunk.get('page')}" or f"{collection_name}_chunk_{i}"
        ids.append(unique_id)

    print(f"Total chunks to process: {len(documents)}")
    

    # Setting maximum batch speed
    max_batch_size = client.get_max_batch_size()
    
    for i in range(0, len(documents), max_batch_size):
        batch_documents = documents[i:i + max_batch_size]
        batch_metadatas = metadatas[i:i + max_batch_size]
        batch_ids = ids[i:i + max_batch_size]
        
        print(f"Embedding chunks {i} to {i + len(batch_documents)}")
        batch_embeddings = model.encode(batch_documents, batch_size = 32, show_progress_bar=True)
        
        collection.upsert(
            documents=batch_documents,
            embeddings = batch_embeddings.tolist(),
            metadatas=batch_metadatas,
            ids=batch_ids
        )
            
    print(f"Collection '{collection_name}' is fully populated.")

if __name__ == "__main__":
    
    constitution_json = Path("Datasets/Processed_data/constitution_chunks.json")
    caselaws_json = Path("Datasets/Processed_data/caselaws_chunks.json")
    
    if constitution_json.exists():
        vector_database(constitution_json, "constitution")
    else:
        print(f"File not found: {constitution_json}")
        
    if caselaws_json.exists():
        vector_database(caselaws_json, "caselaws")
    else:
        print(f"File not found: {caselaws_json}")