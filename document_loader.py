# upload_page.py
from flask import Blueprint, render_template, request, jsonify 
import os 
from werkzeug.utils import secure_filename 

upload_page = Blueprint('upload_page', __name__, template_folder='templates') 
UPLOAD_FOLDER = 'uploaded_documents' 
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'} 

def allowed_file(filename): 
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 

@upload_page.route('/', methods=['GET']) 
def upload_form(): 
    # Renders templates/upload.html 
    return render_template('upload.html') 

@upload_page.route('/file', methods=['POST']) 
def upload_file(): 
    if 'file' not in request.files: 
        return jsonify({"message": "No file part in the request"}), 400 
    file = request.files['file'] 
    if file.filename == '': 
        return jsonify({"message": "No file selected for uploading"}), 400 
    if file and allowed_file(file.filename): 
        filename = secure_filename(file.filename) 
        file_path = os.path.join(UPLOAD_FOLDER, filename) 
        file.save(file_path) 
        return jsonify({"message": f"File {filename} uploaded successfully."}) 
    else: 
        return jsonify({"message": "Invalid file type. Allowed types are pdf, docx, txt"}), 400 

 