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
    UPLOAD_INSTRUCTIONS = '<b>Upload Instructions:</b> Upload the files you want to process. You can upload multiple files at once. <br><b>Supported file types:</b> .pdf, .txt, .docx. <br>Get your documents. Anything you have as a class doc or optional reading or related reading - pdf, doc, docx, .tex, txt all work. For pdf documents you cannot copy/paste from, will not load right, so you will need to use an online free OCR software to convert the pdf to something readable first. A lot of economics working papers (including mine!) are in a format that does really bad (famously the letter "f" will not copy/paste right) - a few errors are not terrible, but basically, anything you have which is not in pdf, you should use the other format. For your slides, write one to two paragraphs of each slide and save this document as a txt file. Related text that is "near" each other is easier to find - for instance, if you syllabus has a table listing when each class is from the first to the last, and what is due when, it will absolutely be searchable perfectly. If it requires five pages of reading to know what, say, the "last" assignment due in a semester is, this will be much harder using our method.'
    RENAME_INSRUCTIONS = '<b>Renaming Instructions:</b> Once you have uploaded the files; Name them in a way that is easy to follow, example: <ul style="text-align:left;"><li> "Bryan and Guzman - Entrepreneurial Migration"</li><li>"Agarwal Gans Goldfarb - Power and Prediction"</li><li>"Class Handout - Startup Venture Financing"</li><li>"Class Lecture Transcription - Experimentation (Class 1)"</li><li>"CDL Advanced Entrepreneurship Class Transcript - Class 2 Pricing for Startups"</li></ul>'
