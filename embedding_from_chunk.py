import chunk 
from langchain.docstore.in_memory import InMemoryDocstore 
from  langchain_community.vectorstores import FAISS #,Chroma 
from langchain.embeddings import HuggingFaceEmbeddings 
from langchain.schema import Document 
import faiss 
import json 
import os  
import numpy as np 

#CHROMA_DIR ="chroma_db" 

FAISS_DIR= r"faiss_db" 
FAISS_INDEX_FILE = os.path.join(FAISS_DIR,"faiss_index.bin") 
FAISS_METADATA_FILE = os.path.join(FAISS_DIR,"faiss_metadata.json") 
 
#initailize embedding  
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") 

#ensure directories exist 
#os.makedirs(CHROMA_DIR,exist_ok=True) 
os.makedirs(FAISS_DIR,exist_ok=True) 

#initialize chroma db 
#chroma_store = Chroma(persist_directory=CHROMA_DIR,embedding_function= embedding_model) 
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
                     "chunk_id":i, 
                     "page_number":chunk["page_number"] 
                 }) 
        for i,chunk in enumerate(chunks) 
    ] 

    if storage_type == "faiss": 
        store_in_faiss(documents) 

 
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

def retrieve_documents_from_faiss(query,n_results=5): 
    results = faiss_store.similarity_search(query=query,k=n_results) 
    return [{ 
        "content":result.page_content, 
        "metadata": result.metadata 
        } for result in results ] 

