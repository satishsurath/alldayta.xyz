import os
import json
import hashlib
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