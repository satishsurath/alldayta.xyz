import os
import json
import hashlib
import shutil
import logging
from app import app
from csv import reader
from flask import session



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
    




# List all the First Level Folders under this app.config["FOLDER_UPLOAD"] + Sessions['folder']
def list_folders():
    try:
        path_to_check = os.path.join(app.config['FOLDER_UPLOAD'], session['folder'])
        app.logger.info(f"Reading from: {path_to_check}")
        return [name for name in os.listdir(path_to_check) if os.path.isdir(os.path.join(path_to_check, name))]
    except Exception as e:
        app.logger.error(f"An exception occurred when reading from: {path_to_check} with error: {e}")
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



def get_content_files(folder_path):
    """Get a list of content files from the given folder, excluding specific and hidden files."""
    return [
        f for f in os.listdir(folder_path) 
        if os.path.isfile(os.path.join(folder_path, f)) 
        and not f.startswith('.')
        and f != 'Textchunks.npy' 
        and f != 'Textchunks-originaltext.csv'
        and f != app.config['ACTIVATIONS_FILE']
    ]
    
def check_and_update_activations_file(folder_path):
    """
    Check and update the course activation status JSON file based on the current content in the specified folder.
    
    Parameters:
    - folder_path (str): Path to the directory containing content files.
    
    Returns:
    - dict: Updated activations with keys being content file names and values being their activation status (True/False).
    
    The function does the following:
    1. Retrieves the list of content files present in the directory, ignoring specific and hidden files.
    2. Loads the existing activations from the ACTIVATIONS_FILE if it exists, otherwise initializes an empty dictionary.
    3. Updates the activations based on the current content, setting the status to False for any new content.
    4. Saves the updated activations back to the ACTIVATIONS_FILE.
    """
    contents = get_content_files(folder_path)
    # Load existing activations if they exist
    activations_path = os.path.join(folder_path, app.config['ACTIVATIONS_FILE'])
    if os.path.exists(activations_path):
        with open(activations_path, 'r') as f:
            activations = json.load(f)
    else:
        activations = {}

    # Update activations based on existing content
    for content in contents:
        if content not in activations:
            activations[content] = False

    # Save updated activations
    with open(activations_path, 'w') as f:
        json.dump(activations, f)

    return activations




def read_csv_preview(file_path):
    try:
        with open(file_path, 'r') as f:
            csv_reader = reader(f)
            next(csv_reader, None)  # Skip the header
            second_row = next(csv_reader, None)  # Get the second row
            
            if second_row and len(second_row) > 1:  # Ensure there's a second element
                return second_row[1]  # Get the second element and return it
            
            else:
                return "No preview data available"  # Return a message if there's no preview data
            
    except Exception as e:
        print(f"Error reading {file_path}: {e}")  # Print any errors encountered
        return "Error reading preview data"  # Return a message if an error was encountered
