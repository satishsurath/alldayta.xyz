import os
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler

from flask import Flask, request, session, has_request_context
from config import Config
from flask_session import Session
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_dropzone import Dropzone

app = Flask(__name__)
app.config.from_object(Config)


# ---------------  Login Manager --------------- #
# Initialize the login manager
login_manager = LoginManager()
login_manager.login_view = 'adminlogin'
login_manager.init_app(app)


# Initialize the session
Session(app)

#Initialize CSFR Protect
csrf = CSRFProtect(app)


# Set up Dropzone
dropzone = Dropzone(app)


from app import routes, file_operations



# ---------------  Configure logging --------------- #

# Overloading the logging formatter to include the request and session data
class CustomFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            record.user_agent = str(request.user_agent)
            record.request_data = f"Request: '{record.url}' [{request.method}]"
            record.session_data = f"Session: {dict(session)}"
        else:
            record.url = None
            record.remote_addr = None
            record.user_agent = None
            record.request_data = None
            record.session_data = None

        return super().format(record)

# Set up file and email logging
def setup_logging():
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Create a separate logger for startup logs
    startup_logger = logging.getLogger('startup_logger')
    startup_logger.setLevel(logging.INFO)
    startup_file_handler = RotatingFileHandler('logs/startup.log', maxBytes=10240, backupCount=10)
    file_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    startup_file_handler.setFormatter(file_formatter)
    startup_logger.addHandler(startup_file_handler)
    
    # Regular logging setup
    file_handler = RotatingFileHandler('logs/alldayta.xyz.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(CustomFormatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]; '
    '%(request_data)s; %(session_data)s; User Agent: %(user_agent)s'
))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    # Log the startup message using the separate logger
    startup_logger.info('--------AllDayTA.xy startup-----------')


# Check if the app is in debug mode
if not app.debug:
    # Set up email error logging
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='ErrorLogFile@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='SummarizeMe.io Failure',
            credentials=auth, secure=secure
        )
        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(CustomFormatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]\n'
            'Request: %(request_data)s\n'
            'Session: %(session_data)s\n'
            'User Agent: %(user_agent)s\n'
        ))
        app.logger.addHandler(mail_handler)

    setup_logging()
else:
    # In Debug mode, we only need the regular file logger.
    setup_logging()