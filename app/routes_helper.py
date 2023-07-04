import hashlib
import os
from pdfminer.high_level import extract_text
from io import BytesIO
from app.forms import UploadSyllabus
from werkzeug.utils import secure_filename
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
    if get_first_txt_file(pdf_path):
        delete_files_in_folder(pdf_path)

    #write the PDF files and text files to the locations:
    if check_folder_exists(pdf_path):
        pdf_file.save(pdf_path)
        with open(txt_path, 'w') as txt_file:
            txt_file.write(course_syllabus)


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
