import os
from flask import Blueprint, request, jsonify,render_template

from langchain.vectorstores import FAISS

from langchain.embeddings import HuggingFaceEmbeddings 
# Blueprint for the chat feature
from  openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
 
chat_page = Blueprint('chat_page', __name__,  template_folder='templates')


# Initialize LLM
llm = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),  # This is the default and can be omitted
)
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

#llm = ChatOpenAI(openai_api_key=api_key, model_name="gpt-4", temperature=0.7)

# FAISS metadata file
FAISS_METADATA_FILE = "faiss_db/faiss_metadata.json"
CHUNK_FOLDER = 'chunked_documents' 
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") 
# FAISS store
faiss_store = FAISS.load_local("faiss_db", embeddings=embedding_model,allow_dangerous_deserialization=True)


@chat_page.route('/', methods=['GET']) 
def chat_form(): 
    # Renders templates/upload.html 
    return render_template('chat.html') 


@chat_page.route('/query', methods=['POST'])
def chat_with_document():
    try:
        # Get the user query
        data = request.json
        query = data.get('query')

        if not query:
            return jsonify({"error": "Query is required"}), 400

        # Retrieve relevant documents from FAISS
        results = query_faiss(query, n_results=3)
        relevant_texts = [res['content'] for res in results]
       
        if not relevant_texts:
            return jsonify({"response": "No relevant information found in the documents."}), 200

        # Prepare LLM input
        context = "\n\n".join(relevant_texts)
        prompt = f"""You are an intelligent assistant. Use the following context to answer the question:
        
        Context:
        {context}

        Question:
        {query}

        Please provide a clear and concise answer based on the context."""

        # Get response from LLM
        response =  llm.chat.completions.create(
                    messages=[
                         {"role": "system", "content": "You are an intelligent assistant. Your responses should be concise and strictly based on the given context."},
                         {"role": "user", "content": prompt}
                    ],
                    model=os.getenv("MODEL"),
                )
        result = response.choices[0].message.content

        return jsonify({"response": result})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

def query_faiss(query, n_results=3):
    """Retrieve relevant documents from FAISS."""
    try:
        
        results = faiss_store.similarity_search(query=query, k=n_results)
        response=[]        
        for doc in results:
            response.append({"content":doc.page_content,"metadata":doc.metadata}) 
            
        return response
    except Exception as e:
        print(f"Error querying FAISS: {e}")
        return []
    
    