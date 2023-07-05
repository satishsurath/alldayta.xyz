import hashlib
import os
from pdfminer.high_level import extract_text
from io import BytesIO
from app.forms import UploadSyllabus
from werkzeug.utils import secure_filename
from app import app
from app.file_operations import (
    read_from_file_json,
    read_from_file_text,
    check_folder_exists,
    list_folders,
    rename_folder,
    delete_folder,
    create_folder,
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
    pdf_path = get_file_path(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name, filename)
    txt_filename = secure_filename(course_syllabus_hash + os.path.splitext(pdf_file.filename)[0] + '.txt')
    txt_path = get_file_path(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name, txt_filename)

    # check if there is a text file already and delete the folder contents
    if get_first_txt_file(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name)):
        delete_files_in_folder(pdf_path)

    #write the PDF files and text files to the locations:
    if check_folder_exists(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name)):
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


# This function checks all sub-folders (courses) in a given parent folder and returns a list of those that contain both 'textchunks.npy' and 'textchunks-originaltext.csv' files.
def courses_with_final_data(parent_folder):
    courses = []
    for course_name in os.listdir(parent_folder):
        course_folder = os.path.join(parent_folder, course_name)
        # Exclude files, hidden folders and specific file names
        if not os.path.isdir(course_folder) or course_name.startswith('.') or course_name in ['textchunks.npy', 'textchunks-originaltext.csv']:
            continue
        file_info = detect_final_data_files(course_folder)
        # Check if both files are present
        if file_info['Textchunks.npy']['present'] and file_info['Textchunks-originaltext.csv']['present']:
            courses.append(course_name)
    return courses