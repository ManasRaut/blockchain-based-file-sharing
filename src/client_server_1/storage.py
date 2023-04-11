import uuid  
import shutil
import os

FILE_LOCATION="../../files"

def add(encrypted_file_path):
	hash = str(uuid.uuid4())
	dest = shutil.copyfile(encrypted_file_path, os.path.join(FILE_LOCATION, hash))
	return hash

def get(file_hash):
	file = open(os.path.join(FILE_LOCATION, file_hash), "rb+")
	file_content = file.read()
	file.close()
	return file_content