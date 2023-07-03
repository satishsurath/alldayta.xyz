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
    get_first_txt_file
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
      return redirect(url_for('index'))
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

@app.route('/delete-item', methods=['POST'])
@login_required
def delete_item():
    name = request.form['name']
    #$print(name)
    course_name = request.form.get('course_name', None)
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
    ################ 
    # Part 1: Upload Syllabus PDF file and Save the text version
    ################ 
    #Check if the form was sucessfully validated:
    if form.validate_on_submit():
      # Get the uploaded PDF file
      pdf_file = form.pdf.data
      course_syllabus  = extract_text(BytesIO(pdf_file.read()))
      course_syllabus_hash = hashlib.sha256(course_syllabus.encode('utf-8')).hexdigest()

      #generate file names and full file paths for the PDF and txt files
      filename = secure_filename(course_syllabus_hash + pdf_file.filename)
      pdf_path = os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name, filename)
      txt_filename = secure_filename(course_syllabus_hash + os.path.splitext(pdf_file.filename)[0] + '.txt')
      txt_path = os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name, txt_filename)

      # check if there is a text file already and delete the folder contents
      if get_first_txt_file(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name)):
        folder_path = os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name)
        for file_name in os.listdir(folder_path):
          file_path = os.path.join(folder_path, file_name)
          delete_file(file_path)

      #write the PDF files and text files to the locations:
      if check_folder_exists(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name)):
          pdf_file.save(pdf_path)
          with open(txt_path, 'w') as txt_file:
              txt_file.write(course_syllabus)
    ################ 
    # Part 2: Load Course Content
    ################ 
    #query all the files in the Upload Folder for the respective course
    folder_path = os.path.join(app.config["FOLDER_UPLOAD"], course_name)
    contents = os.listdir(folder_path) if os.path.exists(folder_path) else []
    ################ 
    # Part 3: Load Syllabus
    ################ 
    # check if we have the Syllabus already for this course
    if get_first_txt_file(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name)):
      print(get_first_txt_file(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name)))
      syllabus = read_from_file_text(get_first_txt_file(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name))).replace('\n', '<br>')
      print(syllabus)
    else:
       syllabus = None

    # we have now processed PDF Uploads, Syllabus Loading, Course Content Loading.
    # Time to load up the template

    return render_template(
       'course_contents.html', 
       course_name=course_name, 
       contents=contents,
       syllabus=syllabus,
       name=session.get('name'), 
       form=form
       )

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




