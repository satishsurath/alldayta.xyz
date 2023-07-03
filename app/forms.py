from flask_wtf import FlaskForm
from wtforms import SubmitField
from flask_wtf.file import FileField, FileRequired, FileAllowed


class UploadSyllabus(FlaskForm):
    pdf = FileField('Upload Course Syllabus (PDF) file:', validators=[FileRequired(), FileAllowed(['pdf'], 'PDF files only')])
    submit = SubmitField('Update Course Syllabus')