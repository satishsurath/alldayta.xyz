import os
import json
import hashlib
import shutil
from app import app


#check if folder exists, if not create it
def check_folder_exists(folder_path):
  try:
    if not os.path.exists(folder_path):
      os.makedirs(folder_path)
    return True
  except:
    return False
  
#Given the filename, read the file and return the json, wrap it in try catch
def read_from_file_json(filename):
    try:
        with open(filename, 'r') as f:
            json_contents = json.load(f)
        return json_contents
    except:
        return False
      
#Given the filename, read the file and return the contents, wrap it in try catch
def read_from_file_text(filename):
    try:
        with open(os.path.join(app.config['FOLDER_PROCESSED_CONTENT'], filename), 'r') as f:
            content = f.read()
        return content
    except:
        return False
    



# List all the First Level Folders under this app.config["FOLDER_UPLOAD"]
def list_folders():
    try:
        return [name for name in os.listdir(app.config["FOLDER_UPLOAD"]) if os.path.isdir(os.path.join(app.config["FOLDER_UPLOAD"], name))]
    except:
        return False

# Rename the Folder (with the Folder Name as its input parameter)
def rename_folder(old_folder_name, new_folder_name):
    try:
        os.rename(os.path.join(app.config["FOLDER_UPLOAD"], old_folder_name), os.path.join(app.config["FOLDER_UPLOAD"], new_folder_name))
        return True
    except:
        return False

# Delete the Folder (and all the contents under this)
def delete_folder(folder_name):
    try:
        shutil.rmtree(os.path.join(app.config["FOLDER_UPLOAD"], folder_name))
        return True
    except:
        return False

# Create a New Folder under this app.config["FOLDER_UPLOAD"]
def create_folder(folder_name):
    try:
        os.makedirs(os.path.join(app.config["FOLDER_UPLOAD"], folder_name))
        return True
    except:
        return False
