import fitz
import vector_store
import database


def extract_text_from_pdf(file_bytes:bytes) ->str:
    text_content=" "
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text_content += page.get_text()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return text_content


def chunk_text(text:str,chunk_size:int=300,overlap:int=50)->list[str]:
    words=text.split()
    if not words:
        return []
    
    chunks=[]
    for i in range(0, len(words), chunk_size - overlap):
        chunk = words[i:i + chunk_size]
        chunks.append(" ".join(chunk))
        
    return chunks


def process_and_index_pdf(doc_id: int, file_bytes: bytes):
    """
    Orchestrator function that now also updates the document's status.
    """
    print(f"--- Starting processing for document ID: {doc_id} ---")
    try:
        text = extract_text_from_pdf(file_bytes)
        if not text:
            raise ValueError("No text could be extracted from the PDF.")

        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("Could not create text chunks from the document.")
            
        print(f"Created {len(chunks)} text chunks for document {doc_id}.")

       
        vector_store.add_document_chunks(doc_id, chunks)
        
        # If everything succeeds, update the status to COMPLETED
        database.update_document_status(doc_id, 'COMPLETED')
        print(f"--- Finished processing successfully for document ID: {doc_id} ---")

    except Exception as e:
        print(f"An error occurred during processing for doc_id {doc_id}: {e}")
        # If any error occurs, update the status to FAILED
        database.update_document_status(doc_id, 'FAILED')

