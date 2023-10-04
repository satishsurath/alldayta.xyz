import hashlib
import os
import time
import openai
import random
from pdfminer.high_level import extract_text
from io import BytesIO
from app.forms import UploadSyllabus
from werkzeug.utils import secure_filename
from app import app
from flask import session
from app.file_operations import (
    read_from_file_json,
    read_from_file_text,
    check_folder_exists,
    list_folders,
    rename_folder,
    delete_folder,
    create_course_folder_with_metadata,
    allowed_file,
    delete_file,
    get_first_txt_file,
    get_file_path,
    delete_files_in_folder

)


# This function handles an uploaded PDF file from a form, extracts text from the PDF, generates a hash of the extracted text for naming, checks if a text file already exists for the course and deletes it if so, and finally saves the PDF and the extracted text to the designated locations.
def save_pdf_and_extract_text(form, course_name):
    # Get the uploaded PDF file
    pdf_file = form.pdf.data
    course_syllabus  = extract_text(BytesIO(pdf_file.read()))
    course_syllabus_hash = hashlib.sha256(course_syllabus.encode('utf-8')).hexdigest()

    #generate file names and full file paths for the PDF and txt files
    filename = secure_filename(course_syllabus_hash + pdf_file.filename)
    user_folder = session['folder']
    pdf_path = get_file_path(app.config['FOLDER_PROCESSED_SYLLABUS'], user_folder, course_name, filename)
    txt_filename = secure_filename(course_syllabus_hash + os.path.splitext(pdf_file.filename)[0] + '.txt')
    txt_path = get_file_path(app.config['FOLDER_PROCESSED_SYLLABUS'], user_folder, course_name, txt_filename)

    # check if there is a text file already and delete the folder contents
    if get_first_txt_file(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], user_folder, course_name)):
        delete_files_in_folder(pdf_path)

    #write the PDF files and text files to the locations:
    if check_folder_exists(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], user_folder, course_name)):
        pdf_file.save(pdf_path)
        with open(txt_path, 'w') as txt_file:
            txt_file.write(course_syllabus)

# This function checks if the '-originaltext.csv' and '-originaltext.npy' versions of each file in the provided list exist in the 'Textchunks' and 'EmbeddedText' folders respectively, and returns their existence status.
def check_processed_files(contents, parent_folder):
    processed_files_info = []
    for file in contents:
        file_without_ext = os.path.splitext(file)[0]
        processed_csv_file_name = file_without_ext + "-originaltext.csv"
        processed_npy_file_name = file_without_ext + "-originaltext.npy"
        processed_csv_file_path = os.path.join(parent_folder, "Textchunks", processed_csv_file_name)
        processed_npy_file_path = os.path.join(parent_folder, "EmbeddedText", processed_npy_file_name)
        csv_exists = os.path.isfile(processed_csv_file_path)
        npy_exists = os.path.isfile(processed_npy_file_path)
        # Add the csv and npy existence check results to the list
        processed_files_info.append([file, csv_exists, npy_exists])
    return processed_files_info

# This function checks if 'textchunks.npy' and 'textchunks-originaltext.csv' files are present in a given course directory, and returns their status (present or not) and size.
def detect_final_data_files(course_name):
    file_info = {}
    for file_name in ['Textchunks.npy', 'Textchunks-originaltext.csv']:
        file_path = os.path.join(course_name, file_name)
        if os.path.isfile(file_path):
            file_info[file_name] = {
                'present': True,
                'name': file_name,
                'size': os.path.getsize(file_path)
            }
        else:
            file_info[file_name] = {
                'present': False,
                'name': file_name,
                'size': None
            }
    return file_info


# Define a retry decorator with exponential backoff
def retry_with_exponential_backoff(func):
    def wrapper(*args, **kwargs):
        max_retries = 5
        retry_delay = 1  # Initial delay in seconds
        for _ in range(max_retries):
            try:
                return func(*args, **kwargs)
            except openai.error.RateLimitError as e:
                print("Rate limit exceeded. Retrying after delay...")
                time.sleep(retry_delay)
                # Increase the delay for the next retry with some random jitter
                retry_delay *= 2 * random.uniform(0.8, 1.2)
        # If max_retries exceeded, raise an exception
        raise Exception("API rate limit exceeded even after retries.")
    return wrapper


# read metadata from the course folder and store them in session variables
def load_course_metadata(metadata):
    # save the values of the metadata in session
    session['classname'] = metadata['classname']
    session['professor'] = metadata['professor']
    session['assistants'] = metadata['assistants']
    session['classdescription'] = metadata['classdescription']
    session['assistant_name'] = metadata['assistant_name']