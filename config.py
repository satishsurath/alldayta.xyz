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
    FOLDER_PREUPLOAD = 'app/preuploads' #folder to store the files uploaded by the user BEFORE Renamed
    FOLDER_UPLOAD = 'app/uploads' #folder to store the files where they are Processed [Chopped, Embnedded, etc.]
    FOLDER_SETTINGS = 'app/settings' #folder to store the settings files
    ACTIVATIONS_FILE = 'CourseContentActivations.JSON' #filename used to store the activation status of course contents
    
    
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
    

    #Placeholders from ReadMe

    RENAME_INSRUCTIONS = '<b>Renaming Instructions:</b> Once you have uploaded the files; Name them in a way that is easy to follow: e.g., "Bryan and Guzman - Entrepreneurial Migration", "Agarwal Gans Goldfarb - Power and Prediction", "Class Handout - Startup Venture Financing", "Class Lecture Transcription - Experimentation (Class 1)", "CDL Advanced Entrepreneurship Class Transcript - Class 2 Pricing for Startups" and so on.'
