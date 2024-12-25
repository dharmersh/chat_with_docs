from langchain.docstore.in_memory import InMemoryDocstore 
from  langchain_community.vectorstores import FAISS ,Chroma 
from langchain.embeddings import HuggingFaceEmbeddings 
from langchain.schema import Document 
import faiss 
from langchain_openai import OpenAI
import os
import json
import numpy as np 

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

CHROMA_DIR = "chroma_db"
FAISS_DIR= r"faiss_db" 
FAISS_INDEX_FILE = os.path.join(FAISS_DIR,"faiss_index.bin") 
FAISS_METADATA_FILE = os.path.join(FAISS_DIR,"faiss_metadata.json") 
 # Directory for storing chunked documents
CHUNK_FOLDER = "chunked_documents"
os.makedirs(CHUNK_FOLDER, exist_ok=True)
#initailize embedding  
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") 

#ensure directories exist 
os.makedirs(CHROMA_DIR,exist_ok=True) 
os.makedirs(FAISS_DIR,exist_ok=True) 

#initialize chroma db 
chroma_store = Chroma(persist_directory=CHROMA_DIR,embedding_function= embedding_model) 

#initalize FAISS 
if os.path.exists(FAISS_INDEX_FILE): 
    print("loading existing faiss index ....") 
    index = faiss.read_index(FAISS_INDEX_FILE) 
    # load meta data from meatadata file 
    if os.path.exists(FAISS_METADATA_FILE): 
        with open(FAISS_METADATA_FILE,'r',encoding='utf-8') as f: 
            metadata = json.load(f) 
    else: 
        metadata=[] 
    docstore = InMemoryDocstore({doc["chunk_id"]:  doc for doc in metadata})   
    index_to_docstore_id = {doc["chunk_id"]:doc["chunk_id"] for doc in metadata}           
else: 
    print("Initializing new faiss index .....") 
    index= faiss.IndexFlatL2(384) # embedding model should match the model 
    docstore= InMemoryDocstore({}) 
    index_to_docstore_id={} 
    
faiss_store= FAISS(embedding_function=embedding_model, 
                   index=index, 
                   docstore=docstore, 
                   index_to_docstore_id=index_to_docstore_id) 

def save_faiss(): 
    faiss_store.save_local(FAISS_DIR) 
    print("FIASS index and metadata saved") 

def embed_chunk_from_file(json_file ,storage_type): 
    storage_type= "faiss" 
    if not os.path.exists(json_file): 
        raise FileNotFoundError(f"Chunk file not found {json_file}") 
    with open(json_file, 'r', encoding='utf-8') as f: 
        chunks = json.load(f) 

    documents = [ 
        Document(page_content= chunk["page_content"], 
                 metadata={ 
                    "fileName":chunk["filename"], 
                     "chunk_id":chunk["chunk_id"], 
                     "page_number":chunk["page_number"] 
                 }) 
        for i,chunk in enumerate(chunks) 
    ] 

    if storage_type == "faiss": 
        store_in_faiss(documents) 
    else:
        store_in_chroma(documents) 

def store_in_faiss(documents): 
    faiss_store.add_documents(documents=documents) 
    #save Metatdata  
    metadata=[] 
    for doc in documents: 
        metadata.append(doc.metadata) 
    if os.path.exists(FAISS_METADATA_FILE): 
        with open(FAISS_METADATA_FILE,'r',encoding="utf-8") as f : 
            file_content = f.read().strip() 
            if file_content: 
                existing_metadata = json.loads(file_content) 
            else: 
                existing_metadata=[] 
    else: 
        existing_metadata=[]     
    metadata.extend(existing_metadata) 
    with open(FAISS_METADATA_FILE,'w',encoding='utf-8') as f: 
        json.dump(metadata,f,ensure_ascii=False,indent=4) 
    save_faiss()  
    print("Data successfully stored in FAISS")  

def store_in_chroma(documents):
    chroma_store.add_documents(documents)
    chroma_store.persist()
    print("Data stored in ChromaDB")

def retrieve_documents_from_faiss(query,n_results=5): 
    results = faiss_store.similarity_search(query=query,k=n_results) 
    return [
        { 
            "content":result.page_content, 
            "metadata": result.metadata 
        } 
        for result in results 
        ] 

def retrieve_documents_from_chroma(query, n_results=3):
    results = chroma_store.similarity_search(query, k=n_results)
    return [
        {
            "content": result.page_content,
            "metadata": result.metadata
        }
        for result in results
    ]
    

def generate_answer(context, query):
    try:
        prompt = f"""
        You are an assistant answering strictly based on the provided context. 
        If the answer is not in the context, respond with:
        'The information is not available in the provided document
        
        Use the following context to answer the query:\n\n{context}\n\nQuery: {query}"""
        response=client(prompt)
        return response
    except Exception as e:
        raise RuntimeError(f"Error generating answer: {str(e)}")
