import os
import json
from flask import Blueprint, request, jsonify
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
from docx import Document

chunk_page = Blueprint('chunk_page', __name__)

UPLOAD_FOLDER = 'uploaded_documents'
CHUNK_FOLDER = 'chunked_documents'
chunking_status = {}  # To track the status of each file

def is_file_chunked(filename):
    chunked_file_path = os.path.join(CHUNK_FOLDER, f"{filename}.json")
    return os.path.exists(chunked_file_path)

def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise RuntimeError(f"Error extracting text from PDF: {str(e)}")

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        raise RuntimeError(f"Error extracting text from DOCX: {str(e)}")

def chunk_file(file_path, output_file):
    # Determine file type based on extension
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    if file_extension == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif file_extension == ".docx":
        text = extract_text_from_docx(file_path)
    elif file_extension == ".txt":
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

    # Use RecursiveCharacterTextSplitter to split the text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)

    # Save chunks to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=4)

    return chunks

def process_files_in_background(filenames):
    for filename in filenames:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
   
        os.makedirs(CHUNK_FOLDER, exist_ok=True)
            
        chunked_file_path = os.path.join(CHUNK_FOLDER, f"{filename}.json")

        chunking_status[filename] = "In Process"

        try:
            chunk_file(file_path, chunked_file_path)
            chunking_status[filename] = "Chunking Complete"
        except Exception as e:
            chunking_status[filename] = f"Error: {str(e)}"

@chunk_page.route('/process', methods=['POST'])
def process_chunk():
    filenames = request.json.get('filenames')
    if not filenames:
        return jsonify({"message": "No filenames provided"}), 400

    # Start background processing
    from threading import Thread
    Thread(target=process_files_in_background, args=(filenames,)).start()

    # Initialize status for files
    for filename in filenames:
        chunking_status[filename] = "In Queue"

    return jsonify({"message": "Chunking started in background", "status": chunking_status})

@chunk_page.route('/status', methods=['GET'])
def get_status():
    return jsonify(chunking_status)