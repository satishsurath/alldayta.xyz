from flask_wtf import FlaskForm
from wtforms import SubmitField
from flask_wtf.file import FileField, FileRequired, FileAllowed


class UploadSyllabus(FlaskForm):
    pdf = FileField('', validators=[FileRequired(), FileAllowed(['pdf'], 'PDF files only')])
    submit = SubmitField('Upload Course Syllabus (PDF) file')

