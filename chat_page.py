from flask import Blueprint,render_template, request, jsonify

chat_page = Blueprint('chat_page',  __name__, template_folder='templates')

@chat_page.route('/', methods=['GET'])
def chat_form():
    # Renders templates/chat.html
    return render_template('chat.html')

@chat_page.route('/chat', methods=['POST'])
def chat_with_document():
    query = request.json.get('query')
    if not query:
        return jsonify({"message": "No query provided"}), 400

    response = {"message": "Chat functionality coming soon!"}
    return jsonify(response)