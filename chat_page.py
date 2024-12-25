from flask import Blueprint, request, jsonify,render_template
from dotenv import load_dotenv
import embedding_from_chunk as embed

load_dotenv()
 
chat_page = Blueprint('chat_page', __name__,  template_folder='templates')


@chat_page.route('/', methods=['GET']) 
def chat_form(): 
    # Renders templates/upload.html 
    return render_template('chat.html') 


@chat_page.route('/query', methods=['POST'])
def chat_with_document():
    try:
        # Get the user query
        data = request.json
        print(data)
        dbType = "faiss"
        query = data.get('query')
        retrive_data = None
        if not query:
            return jsonify({"error": "Query is required"}), 400

        if dbType == 'faiss':
            retrive_data = embed.retrieve_documents_from_faiss(query)
        else:
            retrive_data = embed.retrieve_documents_from_chroma(query)
        
        result = embed.generate_answer(retrive_data,query=query)
        
        return jsonify({"response": result})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

