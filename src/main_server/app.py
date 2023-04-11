import os
import urllib.request
from my_constants import app
import pyAesCrypt
from flask import Flask, flash, request, redirect, render_template, url_for, jsonify
from flask_socketio import SocketIO, send, emit
from werkzeug.utils import secure_filename
import socket
import pickle
from blockchain import Blockchain
import storage as Storage
import requests


socketio = SocketIO(app)
blockchain = Blockchain()

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
    print(saved_file)
    return saved_file


# -------------------- Flask routes --------------------


# Home page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('index.html')

# Upload page
@app.route('/upload')
def upload():
    return render_template('upload.html' , message = "Welcome!")

# Download page
@app.route('/download')
def download():
    return render_template('download.html' , message = "Welcome!")

# Main dashboard
@app.route('/connect_blockchain')
def connect_blockchain():
    is_chain_replaced = blockchain.replace_chain()
    return render_template('connect_blockchain.html', chain = blockchain.chain, nodes = len(blockchain.nodes))

# error page
@app.errorhandler(413)
def entity_too_large(e):
    return render_template('upload.html' , message = "Requested Entity Too Large!")



# -------------------- api routes --------------------

# endpoint to upload file and add new block in blockchain
@app.route('/add_file', methods=['POST'])
def add_file():

    # sync the chain
    is_chain_replaced = blockchain.replace_chain()

    # Debug statements
    if is_chain_replaced:
        print('Updated')
    else:
        print('Already latest.')

    if request.method == 'POST':
        error_flag = True

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
                receiver = request.form['receiver_name']
                file_key = request.form['file_key']

                try:
                    # store the file and get its address hash
                    hashed_output1 = hash_user_file(file_path, file_key)
                    # add new block in blockchain
                    index = blockchain.add_file(sender, receiver, hashed_output1)
                except Exception as err:
                    message = str(err)
                    error_flag = True
                    if "ConnectionError:" in message:
                        message = "Gateway down or bad Internet!"
            else:
                error_flag = True
                message = 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'
    
        # return reponse 
        if error_flag == True:
            return render_template('upload.html' , message = message)
        else:
            return render_template('upload.html' , message = "File succesfully uploaded")


# route to download file
@app.route('/retrieve_file', methods=['POST'])
def retrieve_file():

    # sync blockchain
    is_chain_replaced = blockchain.replace_chain()

    # Debug statements
    if is_chain_replaced:
        print('Updated')
    else:
        print('Already latest.')

    if request.method == 'POST':

        error_flag = True

        if request.form['file_hash'] == '':
            message = 'No file hash entered.'
        elif request.form['file_key'] == '':
            message = 'No file key entered.'
        else:
            error_flag = False
            # get form data
            file_key = request.form['file_key']
            file_hash = request.form['file_hash']
            try:
                # get stored file by its hash address
                file_path = retrieve_from_hash(file_hash, file_key)
            except Exception as err:
                message = str(err)
                error_flag = True
                if "ConnectionError:" in message:
                    message = "Gateway down or bad Internet!"

        # get response
        if error_flag == True:
            return render_template('download.html' , message = message)
        else:
            return render_template('download.html' , message = "File successfully downloaded")


# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200


# -------------------- socket events --------------------

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    print(request)

@socketio.on('add_client_node')
def handle_node(client_node):
    print(client_node)
    blockchain.nodes.add(client_node['node_address'])
    emit('my_response', {'data': pickle.dumps(blockchain.nodes)}, broadcast = True)

@socketio.on('remove_client_node')
def handle_node(client_node):
    print(client_node)
    blockchain.nodes.remove(client_node['node_address'])
    emit('my_response', {'data': pickle.dumps(blockchain.nodes)}, broadcast = True)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    print(request)


# run the server
if __name__ == '__main__':
    socketio.run(app, host = '127.0.0.1', port= 5111)