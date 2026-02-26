import json
import chromadb
from pathlib import Path
from chromadb.utils import embedding_functions

def vector_database(json_filepath, collection_name, db_path="./sherialens_db"):
    print(f"Loading data into '{collection_name}'")
    with open(json_filepath, "r", encoding="utf-8") as f:
        knowledge_base = json.load(f)

    client = chromadb.PersistentClient(path=db_path)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = client.get_or_create_collection(name=collection_name, embedding_function=sentence_transformer_ef)
    documents = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(knowledge_base):
        documents.append(chunk["text"])
        metadata = {k: str(v) for k, v in chunk.items() if k != "text" and v is not None}
        metadatas.append(metadata)
        
        # Creating a Unique ID for UPSERT to prevent duplicates
        unique_id = chunk.get("article") or f"{chunk.get('case_name')}_page_{chunk.get('page')}" or f"{collection_name}_chunk_{i}"
        ids.append(unique_id)

    print("Generating embeddings")

    # Dealing with the maximum batch size 
    max_batch_size = client.get_max_batch_size()
    for i in range(0, len(documents), max_batch_size):
        batch_documents = documents[i:i + max_batch_size]
        batch_metadatas = metadatas[i:i + max_batch_size]
        batch_ids = ids[i:i + max_batch_size]
        print(f"Upserting batch {i} to {i + len(batch_documents)}")
    
        collection.upsert(
            documents=batch_documents,
            metadatas=batch_metadatas,
            ids=batch_ids
    )
    
    print(f"Collection '{collection_name}' is fully populated.")

if __name__ == "__main__":
    
    constitution_json = Path("Datasets/Processed_data/constitution_chunks.json")
    caselaws_json = Path("Datasets/Processed_data/caselaws_chunks.json")
    
    # The Constitution Collection
    if constitution_json.exists():
        vector_database(constitution_json, "constitution")
    else:
        print(f"File not found: {constitution_json}")
        
    # The Case Laws Collection
    if caselaws_json.exists():
        vector_database(caselaws_json, "caselaws")
    else:
        print(f"File not found: {caselaws_json}")