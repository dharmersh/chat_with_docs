# File: index_page.py
import os
from flask import Blueprint, render_template

index_page = Blueprint('index_page', __name__)

UPLOAD_FOLDER = 'uploaded_documents'

@index_page.route('/')
def index():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('index.html', files=files)
