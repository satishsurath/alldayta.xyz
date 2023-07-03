import os
import openai
from app import app, login_manager
from flask import render_template, flash, redirect, url_for, request, session

#Secure against CSRF attacks
from flask_wtf.csrf import generate_csrf

from flask_login import login_required, current_user, UserMixin
from flask_login import login_user, logout_user, login_required

from app.file_operations import read_from_file_json, read_from_file_text, check_folder_exists, list_folders, rename_folder, delete_folder, create_folder


# -------------------- Flask app configurations --------------------

openai.api_key = os.getenv("OPENAI_API_KEY")



# -------------------- Basic Admin Authentication --------------------

#Define the Username and Password to access the Logs
#alldayta_User = os.getenv("alldayta_User") or "user1"
#alldayta_Password = os.getenv("alldayta_Password") or "pass1"
#users = {alldayta_User:{'pw':alldayta_Password}}

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
    name = request.form['name']
    create_folder(name)
    return redirect(url_for('course_management'))

@app.route('/rename-item', methods=['POST'])
@login_required
def rename_item():
    old_name = request.form['old_name']
    new_name = request.form['new_name']
    course_name = request.form.get('course_name', None)
    if course_name:
        # This is a file (content) within a course (folder)
        old_path = os.path.join(app.config["FOLDER_UPLOAD"], course_name, old_name)
        new_path = os.path.join(app.config["FOLDER_UPLOAD"], course_name, new_name)
    else:
        # This is a course (folder)
        old_path = os.path.join(app.config["FOLDER_UPLOAD"], old_name)
        new_path = os.path.join(app.config["FOLDER_UPLOAD"], new_name)
    rename_folder(old_path, new_path)  # Replace with the appropriate function to rename a file or folder
    return redirect(request.referrer)

@app.route('/delete-item', methods=['POST'])
@login_required
def delete_item():
    name = request.form['name']
    course_name = request.form.get('course_name', None)
    if course_name:
        # This is a file (content) within a course (folder)
        path = os.path.join(app.config["FOLDER_UPLOAD"], course_name, name)
    else:
        # This is a course (folder)
        path = os.path.join(app.config["FOLDER_UPLOAD"], name)
    delete_folder(path)  # Replace with the appropriate function to delete a file or folder
    return redirect(request.referrer)


@app.route('/course-contents/<course_name>', methods=['GET'])
@login_required
def course_contents(course_name):
    folder_path = os.path.join(app.config["FOLDER_UPLOAD"], course_name)
    contents = os.listdir(folder_path) if os.path.exists(folder_path) else []
    return render_template('course_contents.html', course_name=course_name, contents=contents)