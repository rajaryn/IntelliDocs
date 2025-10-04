import chromadb
from sentence_transformers import SentenceTransformer

# --- INITIALIZATION ---

# Load the embedding model. This is done only ONCE when the application starts.
# 'all-MiniLM-L6-v2' is a great, fast, and lightweight model for getting started.
print("Loading embedding model...")
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
print("Embedding model loaded.")

# Initialize the ChromaDB client.
# We'll use a persistent client that saves the database to a folder named 'chroma_db'
CHROMA_CLIENT = chromadb.PersistentClient(path="./chroma_db")

# Get or create a "collection" which is like a table in a SQL database.
DOCUMENT_COLLECTION = CHROMA_CLIENT.get_or_create_collection(name="documents")


# --- THE MAIN FUNCTIONS ---

def add_document_chunks(doc_id: int, chunks: list[str]):
    """
    Creates embeddings for a list of text chunks and adds them to the vector store.
    """
    if not chunks:
        print(f"No chunks provided for doc_id {doc_id}. Nothing to add.")
        return

    print(f"Creating {len(chunks)} embeddings for doc_id {doc_id}...")
    try:
        # 1. Create embeddings for each chunk in a single batch operation
        embeddings = EMBEDDING_MODEL.encode(chunks).tolist()
        
        # 2. Prepare metadata for each chunk. This is crucial for filtering.
        #    We store the document ID so we can search within a specific document later.
        metadatas = [{'doc_id': str(doc_id)} for _ in chunks]
        
        # 3. Create unique IDs for each chunk to store in ChromaDB.
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        
        # 4. Add all the data to the collection.
        DOCUMENT_COLLECTION.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Successfully added {len(chunks)} chunks for doc_id {doc_id} to the vector store.")

    except Exception as e:
        print(f"An error occurred during embedding or adding to vector store: {e}")


def search_document(doc_id: int, query_text: str, top_k: int = 5) -> list:
    """
    Searches for the most relevant text chunks within a specific document.
    """
    try:
        # 1. Create an embedding for the user's query.
        query_embedding = EMBEDDING_MODEL.encode([query_text]).tolist()
        
        # 2. Query the collection.
        results = DOCUMENT_COLLECTION.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            # This 'where' clause is the magic: it filters to only search
            # chunks that belong to the specified document ID.
            where={"doc_id": str(doc_id)}
        )
        
        # The result is a list of lists, so we get the first item.
        return results['documents'][0] if results['documents'] else []

    except Exception as e:
        print(f"An error occurred during search: {e}")
        return []