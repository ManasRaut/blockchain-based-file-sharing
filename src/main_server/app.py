import os
import urllib.request
from my_constants import app
import pyAesCrypt
from flask import Flask, flash, request, redirect, render_template, url_for, jsonify, send_file
from werkzeug.utils import secure_filename
import pickle
import storage as Storage
from io import BytesIO

# allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# add file extension
def append_file_extension(uploaded_file, file_path):
    file_extension = uploaded_file.filename.rsplit('.', 1)[1].lower()
    user_file = open(file_path, 'a')
    user_file.write('\n' + file_extension)
    user_file.close()

# decrypt file
def decrypt_file(file_path, file_key):
    encrypted_file = file_path + ".aes"
    os.rename(file_path, encrypted_file)
    pyAesCrypt.decryptFile(encrypted_file, file_path,  file_key, app.config['BUFFER_SIZE'])

# encrypt file
def encrypt_file(file_path, file_key):
    pyAesCrypt.encryptFile(file_path, file_path + ".aes",  file_key, app.config['BUFFER_SIZE'])

# store file and get its address hash
def hash_user_file(user_file, file_key):
    encrypt_file(user_file, file_key)
    encrypted_file_path = user_file + ".aes"
    file_hash = Storage.add(encrypted_file_path)
    return file_hash

# retreive file by using its address hash
def retrieve_from_hash(file_hash, file_key):
    file_content = Storage.get(file_hash)
    file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], file_hash)
    user_file = open(file_path, 'ab+')
    user_file.write(file_content)
    user_file.close()
    decrypt_file(file_path, file_key)
    with open(file_path, 'rb') as f:
        lines = f.read().splitlines()
        last_line = lines[-1]
    user_file.close()
    file_extension = last_line
    saved_file = file_path + '.' + file_extension.decode()
    os.rename(file_path, saved_file)
    return saved_file


# -------------------- Flask routes --------------------


# Home page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('index.html')

# Main dashboard
@app.route('/connect_blockchain')
def connect_blockchain():
    return render_template('connect_blockchain.html')

# error page
@app.errorhandler(413)
def entity_too_large(e):
    return render_template('upload.html' , message = "Requested Entity Too Large!")



# -------------------- api routes --------------------

# endpoint to upload file and add new block in blockchain
@app.route('/add_file', methods=['POST'])
def add_file():
    if request.method == 'POST':
        
        # check if file is undefined
        if 'file' not in request.files:
            message = 'No file part'
        else:
            user_file = request.files['file']
            # check if no file is uploaded
            if user_file.filename == '':
                message = 'No file selected for uploading'

            # check if it is valid file (i.e, meets required extensions)
            if user_file and allowed_file(user_file.filename):
                error_flag = False
                filename = secure_filename(user_file.filename)
                # save the file in upload folder
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                user_file.save(file_path)
                append_file_extension(user_file, file_path)
                # retrieve sent form data
                sender = request.form['sender_name']
                file_key = request.form['file_key']
                try:
                    # store the file and get its address hash
                    hashed_output1 = hash_user_file(file_path, file_key)
                    return jsonify({"status" : "success","message":"File uploaded", "hash":hashed_output1})
                except Exception as err:
                    message = str(err)
            else:
                message = 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'

        return jsonify({"status" : "failed","message":message})


# route to download file
@app.route('/retrieve_file', methods=['POST'])
def retrieve_file():

    if request.method == 'POST':
        if request.form['file_hash'] == '':
            message = 'No file hash entered.'
        elif request.form['file_key'] == '':
            message = 'No file key entered.'
        else:
            # get form data
            file_key = request.form['file_key']
            file_hash = request.form['file_hash']
            try:
                # get stored file by its hash address
                file_path = retrieve_from_hash(file_hash, file_key)
                buf = BytesIO()
                with open(file_path, "rb") as fh:
                    buf = BytesIO(fh.read())
                buf.seek(0)
                return send_file(buf, as_attachment=True, download_name=file_path.split("/")[-1])
            except Exception as err:
                print(err)
                message = str(err)
        return send_file( BytesIO(), as_attachment=True, download_name="file.unknown")


# run the server
if __name__ == '__main__':
    app.run(host = '127.0.0.1', port= 5111)