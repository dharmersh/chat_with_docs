from flask import Flask
from index_page import index_page
from document_loader import upload_page
from document_chunk import chunk_page
from chat_page import chat_page

app = Flask(__name__)

# Register blueprints
app.register_blueprint(index_page)
app.register_blueprint(upload_page, url_prefix="/upload")
app.register_blueprint(chunk_page, url_prefix="/chunk")
app.register_blueprint(chat_page, url_prefix="/chat")

if __name__ == '__main__':
    app.run(debug=True,host="127.0.0.1" ,port=5001)
