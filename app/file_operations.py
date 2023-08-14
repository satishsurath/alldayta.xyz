import os
import json
import hashlib
import shutil
import logging
from app import app



SETTINGS_PATH = os.path.join(app.config['FOLDER_SETTINGS'], 'platform-settings.json')




#check if folder exists, if not create it
def check_folder_exists(folder_path):
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        return True
    except Exception as e:
        print("An exception occurred:", e)
        return False

#check if there is a text file and return the filename
def get_first_txt_file(folder_path):
    try:
        txt_files = [file for file in os.listdir(folder_path) if file.endswith('.txt')]
        if txt_files:
            return os.path.join(folder_path, txt_files[0])
        else:
            return None
    except Exception as e:
        print("An exception occurred:", e)
        return None

#Given the filename, read the file and return the json, wrap it in try catch
def read_from_file_json(filename):
    try:
        with open(filename, 'r') as f:
            json_contents = json.load(f)
        return json_contents
    except Exception as e:
        print("An exception occurred:", e)
        return False

#Given the filename and aata, write the the json, wrap it in try catch
def write_to_file_json(filename, data):
    try:
        app.logger.info(f"Data to be written: {data}")
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        app.logger.info(f"Data successfully written to {filename}")
        with open(filename, 'r') as f:
            read_data = json.load(f)
        app.logger.info(f"Data read back after write: {read_data}")
        absolute_path = os.path.abspath(filename)
        app.logger.info(f"Writing to: {absolute_path}")
        return True
    except Exception as e:
        app.logger.error(f"An exception occurred when writing to {filename}: {e}")
        return False


#Given the filename, read the file and return the contents, wrap it in try catch
def read_from_file_text(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        print("An exception occurred:", e)
        return False
    




# List all the First Level Folders under this app.config["FOLDER_UPLOAD"]
def list_folders():
    try:
        return [name for name in os.listdir(app.config["FOLDER_UPLOAD"]) if os.path.isdir(os.path.join(app.config["FOLDER_UPLOAD"], name))]
    except:
        return False

# Rename the Folder (with the Folder Name as its input parameter)
def rename_folder(old_folder_name, new_folder_name):
    old_folder_path = os.path.abspath(os.path.join(old_folder_name))
    new_folder_path = os.path.abspath(os.path.join(new_folder_name))
    try:
        os.rename(old_folder_path, new_folder_path)
        return True
    except Exception as e:
        print("An exception occurred:", e)
        return False

# Delete the Folder (and all the contents under this)
def delete_folder(folder_name):
    folder_path = os.path.abspath(os.path.join(folder_name))
    #print(folder_path)
    try:
        shutil.rmtree(folder_path)
        return True
    except Exception as e:
        print("An exception occurred:", e)
        return False

# Delete the File
def delete_file(file_name):
    file_path = os.path.abspath(file_name)
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        print("An exception occurred:", e)
        return False

# Create a New Folder under this app.config["FOLDER_UPLOAD"]
def create_folder(folder_name):
    try:
        os.makedirs(os.path.join(app.config["FOLDER_UPLOAD"], folder_name))
        return True
    except:
        return False

#define the allowed files!
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','doc','docx','ppt','pptx'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_path(folder, course_name, filename=''):
    """
    This function generates a full file path.

    Parameters:
    folder (str): The folder path.
    course_name (str): The name of the course.
    filename (str): The filename. Defaults to ''.

    Returns:
    str: The full file path.
    """
    return os.path.join(folder, course_name, filename)


def delete_files_in_folder(folder_path):
    """
    This function deletes all files in a folder.

    Parameters:
    folder_path (str): The folder path.

    Returns:
    None
    """
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    except Exception as e:
        print(f'Failed to delete: Reason: {e}')

    
