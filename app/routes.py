import os
import openai
from app import app, login_manager
from flask import render_template, flash, redirect, url_for, request, session

#Secure against CSRF attacks
from flask_wtf.csrf import generate_csrf

from flask_login import login_required, current_user, UserMixin
from flask_login import login_user, logout_user, login_required


from app.file_operations import read_from_file_json, read_from_file_text, check_folder_exists

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


# Routes for the login and logout pages
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

