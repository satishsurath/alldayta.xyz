import os
import openai
import hashlib
from app import app, login_manager
from flask import render_template, flash, redirect, url_for, request, session

#Secure against CSRF attacks
from flask_wtf.csrf import generate_csrf
from flask_wtf.csrf import CSRFProtect
from flask_login import login_required, current_user, UserMixin
from flask_login import login_user, logout_user, login_required
from werkzeug.utils import secure_filename
from app.forms import UploadSyllabus
from app.routes_helper import (
    save_pdf_and_extract_text, 
    check_processed_files,
    detect_final_data_files,
    courses_with_final_data
)
from app.chop_documents import chunk_documents_given_course_name
from app.embed_documents import embed_documents_given_course_name
from app.create_final_data import create_final_data_given_course_name
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

from pdfminer.high_level import extract_text
from io import BytesIO



# -------------------- Flask app configurations --------------------

openai.api_key = os.getenv("OPENAI_API_KEY")


# -------------------- Basic Admin Authentication --------------------

#Define the Username and Password to access the Logs
users = read_from_file_json(os.path.join(app.config['FOLDER_SETTINGS'], "users.json")) 

## Debug
# print(users)

class User(UserMixin):
  pass

#Define the Username and Password to access the Logs and Debugging  
@login_manager.user_loader
def user_loader(username):
  if username not in users:
    return None
  user = User()
  user.id = username
  return user

@login_manager.request_loader
def request_loader(request):
  username = request.form.get('username')
  if username not in users:
    return None
  user = User()
  user.id = username
  user.is_authenticated = request.form['pw'] == users[username]['pw']
  return user




# -------------------- Routes --------------------
@app.route('/')
@app.route('/index')
def index():
  #return render_template('index.html')
  return render_template('index.html', name=session.get('name'))

@app.route('/privacy-policy')
def privacypolicy():
    return render_template('privacy.html')


#  --------------------Routes for the login and logout pages --------------------
@app.route('/admin-login', methods=['GET', 'POST'])
def adminlogin():
  if request.method == 'POST':
    username = request.form.get('username')
    if request.form.get('pw') == users.get(username, {}).get('pw'):
      user = User()
      user.id = username
      login_user(user)
      session['name'] = user.id
      return redirect(url_for('course_management'))
  return render_template('adminlogin.html', name=session.get('name'))
  
@app.route('/logout')
def logout():
  logout_user()
  session.clear()  # Clear session data
  return redirect(url_for('index'))

#  --------------------Routes for Course Management --------------------

@app.route('/course-management', methods=['GET'])
@login_required
def course_management():
    courses = list_folders()
    return render_template('course_management.html', courses=courses, name=session.get('name'))

@app.route('/create-course', methods=['POST'])
@login_required
def create_course():
    name = request.form['name'].replace(' ', '-')
    create_folder(name)
    return redirect(url_for('course_management'))

@app.route('/rename-item', methods=['POST'])
@login_required
def rename_item():
    old_name = request.form['old_name']
    new_name = request.form['new_name'].replace(' ', '-')
    course_name = request.form.get('course_name', None)
    if course_name:
        # This is a file (content) within a course (folder)
        old_path = os.path.join(app.config["FOLDER_UPLOAD"], course_name, old_name)
        new_path = os.path.join(app.config["FOLDER_UPLOAD"], course_name, new_name)
        rename_folder(old_path, new_path)  # Replace with the appropriate function to rename a file or folder
    else:
        # This is a course (folder)
        # First rename the Course Folder in the "Upload" Section
        old_path_upload = os.path.join(app.config["FOLDER_UPLOAD"], old_name)
        new_path_upload = os.path.join(app.config["FOLDER_UPLOAD"], new_name)
        rename_folder(old_path_upload, new_path_upload)  # Replace with the appropriate function to rename a file or folder
        # Second rename the Course Folder in the "Processed Content" Section
        old_path_processed_content = os.path.join(app.config["FOLDER_PROCESSED_CONTENT"], old_name)
        new_path_processed_content = os.path.join(app.config["FOLDER_PROCESSED_CONTENT"], new_name)
        rename_folder(old_path_processed_content, new_path_processed_content)  # Replace with the appropriate function to rename a file or folder
        # Third rename the Course Folder in the "Processed SAyllabus" Section
        old_path_processed_syllabus = os.path.join(app.config["FOLDER_PROCESSED_SYLLABUS"], old_name)
        new_path_processed_syllabus = os.path.join(app.config["FOLDER_PROCESSED_SYLLABUS"], new_name)        
        rename_folder(old_path_processed_syllabus, new_path_processed_syllabus)  # Replace with the appropriate function to rename a file or folder
    return redirect(request.referrer)

@app.route('/delete-item', methods=['GET'])
@login_required
def delete_item():
    name = request.args.get('name')
    #$print(name)
    course_name = request.args.get('course_name', None)
    if course_name: # So this is a deletion of a single file
        # This is a file (content) within a course (folder)
        path = os.path.join(app.config["FOLDER_UPLOAD"], course_name, name)
        delete_file(path)
    else: # So this is a deletion of a folder
        # This is a course (folder)
        # Delete all the Corresponding Course folders in all places
        path = os.path.join(app.config["FOLDER_UPLOAD"], name)
        delete_folder(path)  
        path = os.path.join(app.config["FOLDER_PROCESSED_CONTENT"], name)
        delete_folder(path)  
        path = os.path.join(app.config["FOLDER_PROCESSED_SYLLABUS"], name)
        delete_folder(path) 
    return redirect(request.referrer)

@app.route('/course-contents/<course_name>', methods=['GET', 'POST'])
@login_required
def course_contents(course_name):
    form = UploadSyllabus()
    # Part 1: Upload Syllabus PDF file and Save the text version: Check if the form was sucessfully validated:
    if form.validate_on_submit():
       save_pdf_and_extract_text(form, course_name)
    # Part 2: Load Course Content: 
    folder_path = os.path.join(app.config["FOLDER_UPLOAD"], course_name)
    #part 3: check for
    print(folder_path)
    file_info = detect_final_data_files(folder_path)
    print(file_info)
    #hiding other folders and hidden files
    if os.path.exists(folder_path):
        #contents = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and not f.startswith('.')]
        contents = [f for f in os.listdir(folder_path) 
            if os.path.isfile(os.path.join(folder_path, f)) 
            and not f.startswith('.') 
            and f != 'textchunks.npy' 
            and f != 'textchunks-originaltext.csv']
    else:
        contents = []
    contents_info = check_processed_files(contents, folder_path)
    if get_first_txt_file(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name)):
      syllabus = read_from_file_text(get_first_txt_file(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name))).replace('\n', '<br>')
    else:
       syllabus = None
    # we have now processed PDF Uploads, Syllabus Loading, Course Content Loading.
    return render_template(
       'course_contents.html', 
       course_name=course_name,
       contents_info = contents_info, 
       contents=contents,
       syllabus=syllabus,
       name=session.get('name'), 
       form=form,
       file_info=file_info
       )

@app.route('/course-syllabus/<course_name>', methods=['GET', 'POST'])
@login_required
def course_syllabus(course_name):
    # check if we have the Syllabus already for this course
    if get_first_txt_file(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name)):
      syllabus = read_from_file_text(get_first_txt_file(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name))).replace('\n', '<br>')
    else:
       syllabus = None
    # we have now processed PDF Uploads, Syllabus Loading, Course Content Loading.
    return render_template(
       'course_syllabus.html', 
       course_name=course_name, 
       syllabus=syllabus,
       name=session.get('name'), 
       )

#This is used by the Flask_Dropone component
@app.route('/upload-file', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        course_name = request.form.get('course_name')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['FOLDER_UPLOAD'], course_name, filename))
        return "File uploaded successfully."
    return render_template('course_contents.html', course_name=course_name, name=session.get('name'))


#  --------------------Routes for Content Processing --------------------

@app.route('/chop-course-content', methods=['GET'])
@login_required
def chop_course_content():
    course_name = request.args.get('course_name', None) 
    chunk_documents_given_course_name(os.path.join(app.config['FOLDER_UPLOAD'], course_name))
    return redirect(request.referrer)

@app.route('/embed-course-content', methods=['GET'])
@login_required
def embed_course_content():
    course_name = request.args.get('course_name', None) 
    embed_documents_given_course_name(os.path.join(app.config['FOLDER_UPLOAD'], course_name))
    return redirect(request.referrer)

@app.route('/create-final-data-course-content', methods=['GET'])
@login_required
def create_final_data_course_content():
    course_name = request.args.get('course_name', None) 
    create_final_data_given_course_name(os.path.join(app.config['FOLDER_UPLOAD'], course_name))
    return redirect(request.referrer)

#  --------------------Routes for Chatting --------------------

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    # check if we have the Syllabus already for this course
    if courses_with_final_data(app.config['FOLDER_UPLOAD']):
      courses = courses_with_final_data(app.config['FOLDER_UPLOAD'])
    else:
       syllabus = None
    # we have now processed PDF Uploads, Syllabus Loading, Course Content Loading.
    return render_template(
       'chat.html', 
       courses=courses, 
       name=session.get('name'), 
       )