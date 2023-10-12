import os
import json
import pandas as pd
import numpy as np
from flask import flash, session
from app import app

def create_final_data_given_course_name(course_name):
    session_course_name = session.get('course_name')
    # Path to the activations file
    app.logger.info(f"Creating final data for course: {course_name}")
    activations_file = os.path.join(course_name, "CourseContentActivations.JSON")
    csv_folder = os.path.join(course_name, "Textchunks")
    npy_folder = os.path.join(course_name, "EmbeddedText")
        
    # Check if activations file exists
    if not os.path.exists(activations_file):
        # Flash message to activate content
        flash("Please Activate the content via the Course Content Page.", "warning")
        app.logger.info(f"Activations file not found: {activations_file} for course: {course_name}")
        return

    # Load activations statuses from the JSON file
    with open(activations_file, "r") as f:
        activations_data = json.load(f)
    # Convert keys from format 'filename.docx' to 'filename' by stripping the file extension
    activations = {key.split('.')[0]: value for key, value in activations_data.items()}
    # Adding a new item for Syllabus file is True if there is a Syllabus file
    contents = os.listdir(course_name)
    for file in contents:
        if file.startswith("Syllabus-" + session_course_name):
            activations[file.split('.')[0]] = True
            break


    app.logger.info(f" The Contents of the activations file: {activations}")

    # Check if all files are deactivated
    if not any(activations.values()):
        try:
            # Flash message to activate content
            flash("All content files are deactivated. Please Activate the content via the Course Content Page.", "warning")
            app.logger.info(f"All content files are deactivated for course: {course_name}")
            # Make os.path.join(course_name, "Textchunks.npy") and os.path.join(course_name, "Textchunks-originaltext.csv") empty files
            open(os.path.join(course_name, "Textchunks.npy"), 'w').close()
            open(os.path.join(course_name, "Textchunks-originaltext.csv"), 'w').close()
        except Exception as e:
            app.logger.info(f"Error while creating empty files for course: {course_name}. Error: {e}")
        return
    # Get the sorted list of CSV and .npy files
    csv_files = sorted([f for f in os.listdir(csv_folder) if f.endswith('.csv')])
    npy_files = sorted([f for f in os.listdir(npy_folder) if f.endswith('.npy')])
        
    # Initialize empty DataFrame and NumPy array for concatenation
    concatenated_csv = pd.DataFrame()
    concatenated_npy = None

    for csv_file, npy_file in zip(csv_files, npy_files):
        file_basename = csv_file.replace('-originaltext.csv', '')
        
        # Check if the file is activated
        if activations.get(file_basename, False):
            # Read the CSV file and concatenate
            app.logger.info(f"Reading file: {csv_file} and {npy_file}")
            csv_path = os.path.join(csv_folder, csv_file)
            csv_data = pd.read_csv(csv_path, encoding='utf-8', escapechar='\\')
            concatenated_csv = pd.concat([concatenated_csv, csv_data], ignore_index=True)
            
            npy_path = os.path.join(npy_folder, npy_file)
            npy_data = np.load(npy_path)
            if concatenated_npy is None:
                concatenated_npy = npy_data
            else:
                concatenated_npy = np.concatenate([concatenated_npy, npy_data], axis=0)


    # Save the concatenated data to the base folder
    concatenated_csv.to_csv(os.path.join(course_name, "Textchunks-originaltext.csv"), encoding='utf-8', escapechar='\\', index=False)
    np.save(os.path.join(course_name, "Textchunks.npy"), concatenated_npy)
    
    print("Files saved: Textchunks-originaltext.csv and Textchunks.npy")
    app.logger.info(f"Files saved: Textchunks-originaltext.csv and Textchunks.npy for course: {course_name}")
    print(f"Textchunks-originaltext.csv dimensions: {concatenated_csv.shape}")
    app.logger.info(f"Textchunks-originaltext.csv dimensions: {concatenated_csv.shape} for course: {course_name}")
    print(f"Textchunks.npy dimensions: {concatenated_npy.shape}")
    app.logger.info(f"Textchunks.npy dimensions: {concatenated_npy.shape} for course: {course_name}")   