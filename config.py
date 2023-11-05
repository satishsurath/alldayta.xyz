import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # Configure secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    #  email server 
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['support@alldayta.xyz']


    # Configure file upload
    FOLDER_PREUPLOAD = 'app/preuploads'
    FOLDER_UPLOAD = 'app/uploads'
    FOLDER_PROCESSED_CONTENT = 'app/content'
    FOLDER_PROCESSED_SYLLABUS = 'app/syllabus'
    FOLDER_SETTINGS = 'app/settings'
    ACTIVATIONS_FILE = 'CourseContentActivations.JSON' #file name used to store the activation status of course contents
    
    
    # Configure session options
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = './sessions'
    SESSION_FILE_THRESHOLD = 100
    SESSION_PERMANENT = False

    # Set up Dropzone
    DROPZONE_ALLOWED_FILE_CUSTOM=True
    DROPZONE_ALLOWED_FILE_TYPE='image/*, .pdf, .txt, .docx'
    DROPZONE_MAX_FILE_SIZE=100 #in MB
    DROPZONE_MAX_FILES=30    
    
