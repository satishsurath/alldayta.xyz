import os
import openai
import pandas as pd
import numpy as np
import hashlib
import time
import threading
import csv
import json


from csv import reader
from app import app, login_manager
from flask import render_template, flash, redirect, url_for, request, session, jsonify

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
    courses_with_final_data, # Checks all (courses) sub-folders returns a list that contain both 'textchunks.npy' and 'textchunks-originaltext.csv' files.
    retry_with_exponential_backoff # Define a retry decorator with exponential backoff
)
from app.chop_documents import chunk_documents_given_course_name
from app.embed_documents import embed_documents_given_course_name
from app.create_final_data import create_final_data_given_course_name
from app.file_operations import (
    read_from_file_json,
    write_to_file_json,
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
    delete_files_in_folder,
    get_content_files,
    check_and_update_activations_file,
    read_csv_preview
)

from pdfminer.high_level import extract_text
from io import BytesIO

# -------------------- Global Variables --------------------
# this lets us load the data only once and to do it in the background while the user types the first q
df_chunks = None
embedding = None
last_session = None

# define the variable to show / hide all the Courses available to the system


SETTINGS_PATH = os.path.join(app.config['FOLDER_SETTINGS'], 'platform-settings.json')

# Load custom settings from JSON
custom_settings = read_from_file_json(SETTINGS_PATH)
for key, value in custom_settings.items():
    app.config[key.upper()] = True if value["Value"] == "True" else False

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
  #return redirect(url_for('adminlogin'))
  #return render_template('index.html')
  print(app.config["SHOWALLCOURSESAVAILABLE"])
  return render_template('index.html', name=session.get('name'), showAllCoursesAvailable=app.config["SHOWALLCOURSESAVAILABLE"])

@app.route('/privacy-policy')
def privacypolicy():
    return render_template('privacy.html')


#  --------------------Routes for the login and logout pages --------------------
@app.route('/admin-login', methods=['GET', 'POST'])
def adminlogin():
    if session.get('name'):
        return redirect(url_for('course_management'))
    else:
        if request.method == 'POST':
            username = request.form.get('username')
            if request.form.get('pw') == users.get(username, {}).get('pw'):
                user = User()
                user.id = username
                login_user(user)
                session['name'] = user.id
                return redirect(url_for('course_management'))
            else:
                flash('Incorrect username or password!', 'error')
    return render_template('adminlogin.html', name=session.get('name'))
  
@app.route('/logout')
def logout():
  logout_user()
  session.clear()  # Clear session data
  return redirect(url_for('adminlogin'))

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


@app.errorhandler(400)
def bad_request_error(error):
    app.logger.error(f"Bad Request Error: {error}")
    return jsonify(success=False, error="Bad Request"), 400


@app.route('/toggle_activation/<course_name>/<file_name>', methods=['POST'])
@login_required
def toggle_activation(course_name, file_name):
    app.logger.info(f"Raw request values: {request.values}")
    app.logger.info(f"Entered toggle_activation for course {course_name} and file {file_name}")    
    try:
        app.logger.info("Starting toggle_activation logic...")
        app.logger.info(f"Entering toggle_activation with course_name: {course_name}, file_name: {file_name}")

        folder_path = os.path.join(app.config["FOLDER_UPLOAD"], course_name)
        activations_path = os.path.join(folder_path, app.config['ACTIVATIONS_FILE'])
        if os.path.exists(activations_path):
            with open(activations_path, 'r') as f:
                activations = json.load(f)
            
            activations[file_name] = not activations.get(file_name, False)
            
            with open(activations_path, 'w') as f:
                json.dump(activations, f)
                
            app.logger.info(f"Updated activations for {file_name}. New status: {activations[file_name]}")

            return jsonify(success=True, status=activations[file_name])
        else:
            app.logger.warning(f"Activation file not found for course: {course_name}")
            return jsonify(success=False, error="Activation file not found!")
    except Exception as e:
        app.logger.error(f"Exception in toggle_activation: {str(e)}", exc_info=True)
        return jsonify(success=False, error=str(e))


@app.route('/course-contents/<course_name>', methods=['GET', 'POST'])
@login_required
def course_contents(course_name):
    form = UploadSyllabus()
    # Part 1: Upload Syllabus PDF file and Save the text version: Check if the form was sucessfully validated:
    if form.validate_on_submit():
       save_pdf_and_extract_text(form, course_name)
    # Part 2: Load Course Content: 
    folder_path = os.path.join(app.config["FOLDER_UPLOAD"], course_name)
    contents = get_content_files(folder_path)
    file_info = detect_final_data_files(folder_path) # for 'textchunks.npy' and 'textchunks-originaltext.csv' if they exist
    activations = check_and_update_activations_file(folder_path)
    contents_info = check_processed_files(contents, folder_path)
    for info in contents_info:
        filename = info[0]
        info.append(activations.get(filename, False))

    if get_first_txt_file(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name)):
      syllabus = read_from_file_text(get_first_txt_file(os.path.join(app.config['FOLDER_PROCESSED_SYLLABUS'], course_name))).replace('\n', '<br>')
    else:
       syllabus = None
    # we have now processed PDF Uploads, Syllabus Loading, Course Content Loading.
    # When checking and updating activations
    
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


@app.route('/preview-chunks/<course_name>', methods=['GET'])
@login_required
def preview_chunks(course_name):
    folder_path = os.path.join(app.config["FOLDER_UPLOAD"], course_name, 'Textchunks')

    # Filter only csv files in the course content folder
    csv_files = [f for f in os.listdir(folder_path) 
        if os.path.isfile(os.path.join(folder_path, f)) 
        and not f.startswith('.') 
        and f.endswith('.csv')]
    
    # Read the second element of the second line of each csv file
    second_entries = []
    for csv_file in csv_files:
        try:
            with open(os.path.join(folder_path, csv_file), 'r') as f:
                csv_reader = reader(f)
                next(csv_reader, None)  # Skip the header
                second_entry = next(csv_reader, None)  # Get the second row
                if second_entry and len(second_entry) > 1:  # Ensure there's a second element
                    second_entry = second_entry[1]  # Get the second element
                second_entries.append(second_entry)
                #print(f"Second row, second element of {csv_file}: {second_entry}")  # Print second row for debugging
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")  # Print any errors encountered
    #print(f"CSV files: {csv_files}\nSecond entries: {second_entries}")
    return render_template('preview_chunks.html', course_name=course_name, zip=zip, csv_files=csv_files, second_entries=second_entries, name=session.get('name'))



@app.route('/preview-chunks-js/<course_name>/<content_name>', methods=['GET'])
@login_required
def preview_chunks_js(course_name, content_name):
    folder_path = os.path.join(app.config["FOLDER_UPLOAD"], course_name, 'Textchunks')
    file_path = os.path.join(folder_path, content_name)
    # Assuming we are reading a CSV with preview content
    preview_data = read_csv_preview(file_path)  # This function should be implemented to read the CSV preview data
    
    return jsonify({'preview_content': preview_data})

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
    try:
        if request.method == 'POST':
            file = request.files.get('file')
            course_name = request.form.get('course_name')
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['FOLDER_UPLOAD'], course_name, filename))
            return "File uploaded successfully."
        return render_template('course_contents.html', course_name=course_name, name=session.get('name'))
    except Exception as e:
        print(f"An error occurred: {str(e)}")

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    settings_data = read_from_file_json(SETTINGS_PATH) or {}
    if request.method == 'POST':
        for setting, details in settings_data.items():
            # Check if setting was submitted in the form and set to "True" if it was, otherwise "False"
            settings_data[setting]["Value"] = "True" if request.form.get(setting) else "False"
            app.logger.info(f"Setting value for {setting}: {settings_data[setting]['Value']}")
        # Save the updated settings to the JSON file
        if write_to_file_json(SETTINGS_PATH, settings_data):
            app.logger.info("Successfully wrote settings to file.")
        else:
            app.logger.error("Failed to write settings to file.")  
        # Update Flask's app.config with the new settings
        for key, value in settings_data.items():
            app.config[key.upper()] = True if value["Value"] == "True" else False
        flash('Settings have been updated!', 'success') 
    return render_template('settings.html', settings=settings_data, name=session.get('name'))

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

@app.route('/pick-course', methods=['GET', 'POST'])
def pick_course():
    type = request.args.get('type', None) 
    # check if we have the Syllabus already for this course
    if courses_with_final_data(app.config['FOLDER_UPLOAD']):
      courses = courses_with_final_data(app.config['FOLDER_UPLOAD'])
    else:
       syllabus = None
    # we have now processed PDF Uploads, Syllabus Loading, Course Content Loading.
    return render_template(
       'pick_course.html', 
       courses=courses, 
       name=session.get('name'),
       type = type,
       showAllCoursesAvailable = app.config["SHOWALLCOURSESAVAILABLE"] 
       )

# Apply the retry decorator to the original function
#@retry_with_exponential_backoff
@app.route('/teaching-assistant', methods=['GET', 'POST'])
def teaching_assistant():
    global df_chunks, embedding
    course_name = request.args.get('course_name', None)     
    course_folder = os.path.join(app.config['FOLDER_UPLOAD'], course_name)
    dataname = os.path.join(course_folder,"Textchunks")
    classname = course_name
    professor = "Placeholder"
    assistants = "Placeholder"
    classdescription = "Placeholder"
    assistant_name = "Placeholder"
    instruct = 'I am an experimental virtual TA for your course in entrepreneurship.  I have been trained with all of your readings, course materials, lecture content, and slides. I am generally truthful, but be aware that there is a large language model in the background and hallucinations are possible. The more precise your question, the better an answer you will get. You may ask me questions in the language of your choice.  If "an error occurs while processing", ask your question again: the servers we use to process these answers are also in beta.'
    num_chunks = 8

    # check if we have the Syllabus already for this course
    if request.method == 'POST':
        with load_lock:
            # Load the text and its embeddings
            print("ok, starting")
            start_time = time.time()  # record the start time
            df_chunks = load_df_chunks(dataname) # get df_chunks from the global
            elapsed_time = time.time() - start_time  # calculate the elapsed time
            print(f"Data loaded. Time taken: {elapsed_time:.2f} seconds")
            original_question = request.form['content1']

            # if there is a previous question and it's not multiple choice or its answer, check to see if the new one is a syllabus q or followup
            # this works OK for now, it will work better with GPT4
            if not (request.form['content1'].startswith('m:') or request.form['content1'].startswith('M:') or request.form['content1'].startswith('a:')):
                # first let's see if it's on the syllabus
                send_to_gpt = []
                send_to_gpt.append({"role": "user",
                                    "content": f"This question is from a student in an {classname} taught by {professor} with the help of {assistants}.  The class is {classdescription}  I want to know whether this question is likely about the logistical details, schedule, nature, teachers, assignments, or syllabus of the course?  Answer Yes or No and nothing else: {request.form['content1']}"})
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    max_tokens=1,
                    temperature=0.0,
                    messages=send_to_gpt
                )
                print("Is this a syllabus question? " + response["choices"][0]["message"]["content"])
                # Construct new prompt if AI says that this is a syllabus question
                if response["choices"][0]["message"]["content"].startswith('Y') or response["choices"][0]["message"][
                    "content"].startswith('y'):
                    # Concatenate the strings to form the original_question value
                    print("It seems like this question is about the syllabus")
                    original_question = "I may be asking about a detail on the syllabus for " + classname + ". " + request.form['content1']
                # This follow-up question works great in 4 BUT NOT WELL WITH 3.5
                else:
                    # if not on the syllabus, and it might be a followup, see if it is
                    if len(request.form['content2'])>1:
                        send_to_gpt = []
                        send_to_gpt.append({"role": "user",
                                            "content": f"Consider this new question from a user: {request.form['content1']}. Their prior question and the response was {request.form['content2']} Would it be helpful to have the context of the previous question and response to answer the new one?  For example, the new question may refer to 'this' or 'that' or 'the company' or 'their' or 'his' or 'her' or 'the paper' or similar terms whose context is not clear if you only know the current question and don't see the previous question and response, or it may ask for more details or to summarize or rewrite or expand on the prior answer in a way that is impossible to do unless you can see the previous answer.  Answer either Yes or No."})
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            max_tokens=1,
                            temperature=0.0,
                            messages=send_to_gpt
                        )
                        print(f"Consider this new question from a user: {request.form['content1']}. Their prior question and the response was {request.form['content2']} Think very logically.  Is the information requested in the new question potentially related to the previous question and response? Answer either Yes or No.")
                        print("Might this be a follow-up? " + response["choices"][0]["message"]["content"])
                        # Construct new prompt if AI says that this is a followup
                        if response["choices"][0]["message"]["content"].startswith('Y') or response["choices"][0]["message"]["content"].startswith('y'):
                           # Concatenate the strings to form the original_question value
                            print("Creating follow-up question")
                            original_question = 'I have a followup on the previous question and response. ' + request.form['content2'] + 'My new question is: ' + request.form['content1']







            # if answer to Q&A, don't embed a new search, just use existing context
            if request.form['content1'].startswith('a:'):
                print("Let's try to answer that question")
                most_similar = grab_last_response()
                title_str = "<p></p>"
                print("Query being used: " + request.form['content1'])
                print("The content we draw on begins " + most_similar[:200])
                elapsed_time = time.time() - start_time  # calculate the elapsed time
                print(f"Original context for question loaded. Time taken: {elapsed_time:.2f} seconds")
            else:
                embedthequery = openai.Embedding.create(
                    model="text-embedding-ada-002",
                    input=original_question
                )
                print("Query we asked is: " + original_question)
                query_embed=embedthequery["data"][0]["embedding"]
                elapsed_time = time.time() - start_time  # calculate the elapsed time
                print(f"Query embedded. Time taken: {elapsed_time:.2f} seconds")

                # function to compute dot product similarity; tested using Faiss library and didn't really help
                def compute_similarity(embedding, userquery):
                   similarities = np.dot(embedding, userquery)
                   return similarities
                # compute similarity for each row and add to new column
                print(len(query_embed))
                df_chunks['similarity'] = np.dot(embedding, query_embed)
                # sort by similarity in descending order
                df_chunks = df_chunks.sort_values(by='similarity', ascending=False)
                # Select the top query_similar_number most similar articles
                most_similar_df = df_chunks.head(num_chunks)
                elapsed_time = time.time() - start_time  # calculate the elapsed time
                print(f"Original query similarity sorted. Time taken: {elapsed_time:.2f} seconds")
                # Drop duplicate rows based on Title and Text columns
                most_similar_df = most_similar_df.drop_duplicates(subset=['Title', 'Text'])
                # Count the number of occurrences of each title in most_similar_df
                title_counts = most_similar_df['Title'].value_counts()
                # Create a new dataframe with title and count columns, sorted by count in descending order
                title_df = pd.DataFrame({'Title': title_counts.index, 'Count': title_counts.values}).sort_values('Count', ascending=False)
                # Filter the titles that appear at least three times
                title_df_filtered = title_df[title_df['Count'] >= 3]
                # Get the most common titles in title_df_filtered
                titles = title_df_filtered['Title'].values.tolist()
                if len(titles) == 1:
                    title_str = f'<span style="float:right;" id="moreinfo"><a href="#" onclick="toggle_visibility(\'sorting\');" style="text-decoration: none; color: black;">&#9776;</a><div id="sorting" style="display:none; font-size: 12px;"> [The most likely related text is "{titles[0]}"]</div></span><p>'
                    title_str_2 = f'The most likely related text is {titles[0]}. '
                elif len(titles) == 0:
                    title_str = "<p></p>"
                    title_str_2 = ""
                else:
                    top_two_titles = titles[:2]
                    title_str = f'<span style="float:right;" id="moreinfo"><a href="#" onclick="toggle_visibility(\'sorting\');" style="text-decoration: none; color: black;">&#9776;</a><div id="sorting" style="display:none; font-size: 12px;"> [The most likely related texts are "{top_two_titles[0]}" and "{top_two_titles[1]}"]</div></span><p>'
                    title_str_2 = f'The most likely related texts are {top_two_titles[0]} and {top_two_titles[1]}. '
                elapsed_time = time.time() - start_time  # calculate the elapsed time
                print(f"Most related texts are {titles[:1]}.")
                most_similar = '\n\n'.join(row[1] for row in most_similar_df.values)








            # I use very low temperature to give most "factual" answer
            if request.form['content1'].startswith('m:'):
                instructions = "You are a very truthful, precise TA in a " + classname + ".  You think step by step. A strong graduate student is using you as a tutor.  The student would like you to prepare a challenging multiple choice question on the requested topic drawing ONLY on the attached context.  You do not have to merely ask about definitions, but can also construct scenarios or creative examples. NEVER refer to 'the attached context' or 'according to the article' or similar. Assume the student has no idea what context you are drawing your question from, and NEVER state the context you are drawing the question from: just state the question, then state options A to D. After the question, write <span style=\"display:none\"> then give your answer and a short explanation, then after your answer and explanation close the span with </span>"
                original_question = "Construct a challenging multiple-choice question to test me on a concept related to " + request.form['content1'][len('m:'):].strip()
                temperature=0.2
                # save question content for response
                truncated_most_similar = most_similar[:3900]
                session['last_session'] = truncated_most_similar
                print("saving old context to session variable")
            elif request.form['content1'].startswith('a:'):
                instructions = "You are a very truthful, precise TA in a " + classname + ".  You think step by step. You are testing a strong graduate student on their knowledge.  The student would like you, using the attached context, to tell them whether they have answered the attached multiple choice question correctly.  Draw ONLY on the attached context for definitions and theoretical content.  Never refer to 'the attached context' or 'the article says that' or other context: just state your answer and the rationale."
                original_question =  request.form['content1'][len('a:'):].strip()
                temperature=0.2
            else:
                instructions = "You are a very truthful, precise TA in a " + classname + ", a " + classdescription + ".  You think step by step. A strong graduate student is asking you questions.  The answer to their query may appear in the attached book chapters, handouts, transcripts, and articles.  If it does, in no more than three paragraphs answer the user's question; you may answer in longer form with more depth if you need it to fully construct a requested numerical example.  Do not restate the question, do not refer to the context where you learned the answer, do not say you are an AI; just answer the question.  Say 'I don't know' if you can't find the answer to the original question in the text below; be very careful to match the terminology and definitions, implicit or explicit, used in the attached context. You may try to derive more creative examples ONLY if the user asks for a numerical example of some type when you can construct it precisely using the terminology found in the attached context with high certainty, or when you are asked for an empirical example or an application of an idea to a new context, and you can construct one using the exact terminology and definitions in the text; remember, you are a precise TA who wants the student to understand but also wants to make sure you do not contradict the readings and lectures the student has been given in class. Please answer in the language of the student's question."
                temperature=0.2
            reply = []
            print("The question sent to GPT is " + original_question)
            print("The related content is: " + most_similar[:1000])
            send_to_gpt = []
            send_to_gpt.append({"role":"system","content":instructions + most_similar})
            send_to_gpt.append({"role":"user","content":original_question})
            response=openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=send_to_gpt
            )
            query = request.form['content1']
            tokens_new = response["usage"]["total_tokens"]
            reply1 = response["choices"][0]["message"]["content"]
            elapsed_time = time.time() - start_time  # calculate the elapsed time
            send_to_gpt = []
            print(f"GPT Response gathered. You used {tokens_new} tokens. Time taken: {elapsed_time:.2f} seconds")
            # check to make sure GPT is happy with the answer
            send_to_gpt.append({"role":"system","content":"Just say 'Yes' or 'No'. Do not give any other answer."})
            send_to_gpt.append({"role":"user","content":f"User: {original_question}  Attendant: {reply1} Was the Attendant able to answer the user's question?"})
            response=openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                max_tokens=1,
                temperature=0.0,
                messages=send_to_gpt
            )
            print("Did we answer the question? " + response["choices"][0]["message"]["content"])
            # if you don't find the answer, grab the most article we think is most related and try to prompt a followup





            if response["choices"][0]["message"]["content"].lower().startswith("no") and not request.form['content1'].startswith('a:'):
                send_to_gpt = []
                # need to reload df_chunks since its order no longer syncs with embeddings
                df_chunks = pd.read_csv(dataname + "-originaltext.csv")
                # get the article that was most related when we couldn't find the answer
                mostcommontitle = title_df["Title"].value_counts().index[0]
                title_counts = title_df["Title"].value_counts()




                # Check if there is more than one entry in title_df and the second most common title appears at least twice
                if len(title_counts) > 1 and title_counts.iloc[1] >= 2:
                    secondmostcommontitle = title_counts.index[1]
                    # now prompt again, giving that article as context
                    followup_input = f'Using {mostcommontitle}: {original_question}'
                    embedthequery2 = openai.Embedding.create(
                        model="text-embedding-ada-002",
                        input=followup_input
                    )
                    query_embed2 = embedthequery2["data"][0]["embedding"]
                    followup_input2 = f'Using {secondmostcommontitle}: {original_question}'
                    embedthequery3 = openai.Embedding.create(
                        model="text-embedding-ada-002",
                        input=followup_input
                    )
                    query_embed3 = embedthequery3["data"][0]["embedding"]
                    # compute similarity for each row and add to new column
                    df_chunks['similarity2'] = np.dot(embedding, query_embed2)
                    df_chunks['similarity3'] = np.dot(embedding, query_embed3)
                    # sort by similarity in descending order
                    df_chunks = df_chunks.sort_values(by='similarity2', ascending=False)
                    # Select the top query_similar_number most similar articles
                    most_similar_df_fhead = df_chunks.head(5)
                    print(df_chunks.head(2))
                    # sort by similarity in descending order
                    df_chunks = df_chunks.sort_values(by='similarity3', ascending=False)
                    # Select the top query_similar_number most similar articles
                    most_similar_df_fhead = pd.concat([most_similar_df_fhead, df_chunks.head(5)], axis=1)
                    print(df_chunks.head(2))
                    elapsed_time = time.time() - start_time  # calculate the elapsed time
                    print(f"Followup queries similarity sorted. Time taken: {elapsed_time:.2f} seconds")
                    # Drop duplicate rows based on Title and Text columns
                    most_similar_df_follow = most_similar_df_fhead.drop_duplicates(subset=['Title', 'Text'])
                    mostcommontitle = mostcommontitle + " and " + secondmostcommontitle
                    most_similar_followup = "The best guess at related texts is/are " + mostcommontitle + '\n\n'.join(
                        row[1] for row in most_similar_df_follow.values)
                    



                else:
                    # now prompt again, giving that article as context
                    followup_input = f'Using {mostcommontitle}: {original_question}'
                    embedthequery2 = openai.Embedding.create(
                        model="text-embedding-ada-002",
                        input=followup_input
                    )
                    query_embed2 = embedthequery2["data"][0]["embedding"]
                    # compute similarity for each row and add to new column
                    df_chunks['similarity2'] = np.dot(embedding, query_embed2)
                    # sort by similarity in descending order
                    df_chunks = df_chunks.sort_values(by='similarity2', ascending=False)
                    # Select the top query_similar_number most similar articles
                    most_similar_df_fhead = df_chunks.head(10)
                    print(df_chunks.head(2))
                    elapsed_time = time.time() - start_time  # calculate the elapsed time
                    print(f"Followup query similarity sorted. Time taken: {elapsed_time:.2f} seconds")
                    # Drop duplicate rows based on Title and Text columns
                    most_similar_df_follow = most_similar_df_fhead.drop_duplicates(subset=['Title', 'Text'])
                    most_similar_followup = "The best guess at related texts is/are " + mostcommontitle + '\n\n'.join(
                        row[1] for row in most_similar_df_follow.values)
                # now prompt again, giving that article as context
                followup_input=f'Using {mostcommontitle}: {original_question}'
                send_to_gpt.append({"role": "system", "content": instructions + most_similar_followup})
                send_to_gpt.append({"role": "user", "content": f'Using {mostcommontitle}: {original_question}'})
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=send_to_gpt
                )
                tokens_new = tokens_new+response["usage"]["total_tokens"]
                reply1 = response["choices"][0]["message"]["content"]
                # check to see if follow-up was answered
                send_to_gpt = []
                send_to_gpt.append(
                    {"role": "system", "content": "Just say 'Yes' or 'No'. Do not give any other answer."})
                send_to_gpt.append({"role": "user",
                                    "content": f"User: {original_question}  Attendant: {reply1} Was the Attendant able to answer the user's question?"})
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    max_tokens=1,
                    temperature=0.0,
                    messages=send_to_gpt
                )

                print("Did we answer the followup question? " + response["choices"][0]["message"]["content"])

                if response["choices"][0]["message"]["content"].lower().startswith("no") and not request.form['content1'].startswith('a:'):
                    reply1="I'm sorry but I cannot answer that question.  Can you rephrase or ask an alternative?"
                tokens_new = tokens_new + response["usage"]["total_tokens"]
                
            reply1=reply1.replace('\n', '<p>')
            reply = reply1 + title_str
            print(tokens_new)
            return reply
        



    else:
        # Start background thread to load data
        thread = threading.Thread(target=background_loading, args=(dataname,))
        thread.start()
    




    if courses_with_final_data(app.config['FOLDER_UPLOAD']):
      courses = courses_with_final_data(app.config['FOLDER_UPLOAD'])
    else:
       syllabus = None
    # we have now processed PDF Uploads, Syllabus Loading, Course Content Loading.
    return render_template(
       'ta.html', 
       courses=courses, 
       name=session.get('name'),
       course_name = course_name,
       instruct = 'I am an experimental virtual TA for your course in <i>' + course_name + '</i>.<br>I have been trained with all of your readings, course materials, lecture content, and slides. <br>I am generally truthful, but be aware that there is a large language model in the background and hallucinations are possible. <br>The more precise your question, the better an answer you will get. You may ask me questions in the language of your choice. <br> If "an error occurs while processing", ask your question again: the servers we use to process these answers are also in beta.'
       )


#  --------------------Functions for Chatting --------------------

# this ensures we load the data before taking an input
load_lock = threading.Lock()

def background_loading(dataname):
    with load_lock:
        global df_chunks, embedding
        df_chunks = load_df_chunks(dataname)
        print("Loaded data from background")

def grab_last_response():
    global last_session
    last_session = session.get('last_session', None)
    print("Ok, we have last session")
    if last_session is None:
        print("I don't know old content")
        last_session = ""
    return last_session

def load_df_chunks(dataname):
    global df_chunks, embedding
    # maybe just save this numpy embedding?
    if embedding is None:
        df_chunks = pd.read_csv(dataname+"-originaltext.csv")
        embedding = np.load(dataname+".npy")
        #print(f"embedding dimensions: {embedding.shape}")
        #print(f"df_chunks dimensions: {df_chunks.shape}")
    else:
        print("Database already loaded")
    return df_chunks


# #-------------------


  

# load_lock = threading.Lock()  
  
# # Function to handle syllabus question  
# def handle_syllabus_question(request_form, classname, professor, assistants, classdescription):  
#     # Similar to the original function code...  
#     send_to_gpt = []  
#     send_to_gpt.append({"role": "user",  
#                         "content": f"This question is from a student in an {classname} taught by {professor} with the help of {assistants}.  The class is {classdescription}  I want to know whether this question is likely about the logistical details, schedule, nature, teachers, assignments, or syllabus of the course?  Answer Yes or No and nothing else: {request_form['content1']}"})  
#     response = openai.ChatCompletion.create(  
#         model="gpt-3.5-turbo",  
#         max_tokens=1,  
#         temperature=0.0,  
#         messages=send_to_gpt  
#     )  
#     return response  
  
# # Function to handle multiple-choice question and answer  
# def handle_multiple_choice(request_form, classname):  
#     # Similar to the original function code...  
#     if request_form['content1'].startswith('a:'):  
#         most_similar = grab_last_response()  
#     else:  
#         embedthequery = openai.Embedding.create(  
#             model="text-embedding-ada-002",  
#             input=request_form['content1']  
#         )  
#         query_embed = embedthequery["data"][0]["embedding"]  
#         df_chunks['similarity'] = np.dot(embedding, query_embed)  
#         df_chunks = df_chunks.sort_values(by='similarity', ascending=False)  
#         most_similar_df = df_chunks.head(num_chunks)  
#         most_similar = '\n\n'.join(row[1] for row in most_similar_df.values)  
#     return most_similar  
  
# # Function to handle user's query on course data  
# def handle_user_query(request_form, classname, classdescription, most_similar):  
#     # Similar to the original function code...  
#     instructions = "You are a very truthful, precise TA in a " + classname + ", a " + classdescription + ".  You think step by step. A strong graduate student is asking you questions.  The answer to their query may appear in the attached book chapters, handouts, transcripts, and articles.  If it does, in no more than three paragraphs answer the user's question; you may answer in longer form with more depth if you need it to fully construct a requested numerical example.  Do not restate the question, do not refer to the context where you learned the answer, do not say you are an AI; just answer the question.  Say 'I don't know' if you can't find the answer to the original question in the text below; be very careful to match the terminology and definitions, implicit or explicit, used in the attached context. You may try to derive more creative examples ONLY if the user asks for a numerical example of some type when you can construct it precisely using the terminology found in the attached context with high certainty, or when you are asked for an empirical example or an application of an idea to a new context, and you can construct one using the exact terminology and definitions in the text; remember, you are a precise TA who wants the student to understand but also wants to make sure you do not contradict the readings and lectures the student has been given in class. Please answer in the language of the student's question."  
#     send_to_gpt = []  
#     send_to_gpt.append({"role":"system","content":instructions + most_similar})  
#     send_to_gpt.append({"role":"user","content":request_form['content1']})  
#     response=openai.ChatCompletion.create(  
#         model="gpt-3.5-turbo",  
#         messages=send_to_gpt  
#     )  
#     return response  
  
# @app.route('/teaching-assistant', methods=['GET', 'POST'])  
# def teaching_assistant():  
#     global df_chunks, embedding  
#     course_name = request.args.get('course_name', None)       
#     course_folder = os.path.join(app.config['FOLDER_UPLOAD'], course_name)  
#     dataname = os.path.join(course_folder,"Textchunks")  
#     classname = course_name  
#     professor = "Placeholder"  
#     assistants = "Placeholder"  
#     classdescription = "Placeholder"  
#     assistant_name = "Placeholder"  
#     instruct = 'I am an experimental virtual TA for your course in entrepreneurship.  I have been trained with all of your readings, course materials, lecture content, and slides. I am generally truthful, but be aware that there is a large language model in the background and hallucinations are possible. The more precise your question, the better an answer you will get. You may ask me questions in the language of your choice.  If "an error occurs while processing", ask your question again: the servers we use to process these answers are also in beta.'  
#     num_chunks = 8  
  
#     if request.method == 'POST':  
#         with load_lock:  
#             # Load the text and its embeddings  
#             print("ok, starting")  
#             start_time = time.time()  # record the start time  
#             df_chunks = load_df_chunks(dataname) # get df_chunks from the global  
#             elapsed_time = time.time() - start_time  # calculate the elapsed time  
#             print(f"Data loaded. Time taken: {elapsed_time:.2f} seconds")  
  
#             syllabus_response = handle_syllabus_question(request.form, classname, professor, assistants, classdescription)  
#             multiple_choice_response = handle_multiple_choice(request.form, classname)  
#             user_query_response = handle_user_query(request.form, classname, classdescription, multiple_choice_response)  
  
#             # Combine the responses and return to user  
#             return user_query_response + syllabus_response + multiple_choice_response  
#     else:  
#         # Start background thread to load data  
#         thread = threading.Thread(target=background_loading, args=(dataname,))  
#         thread.start()  
          
#         if courses_with_final_data(app.config['FOLDER_UPLOAD']):  
#             courses = courses_with_final_data(app.config['FOLDER_UPLOAD'])  
#         else:  
#             syllabus = None  
#         # We have now processed PDF Uploads, Syllabus Loading, Course Content Loading.  
#         return render_template(  
#             'ta.html',   
#             courses=courses,   
#             name=session.get('name'),  
#             course_name = course_name,  
#             instruct = 'I am an experimental virtual TA for your course in <i>' + course_name + '</i>.<br>I have been trained with all of your readings, course materials, lecture content, and slides. <br>I am generally truthful, but be aware that there is a large language model in the background and hallucinations are possible. <br>The more precise your question, the better an answer you will get. You may ask me questions in the language of your choice. <br> If "an error occurs while processing", ask your question again: the servers we use to process these answers are also in beta.'  
#         )  
