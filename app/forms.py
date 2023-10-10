from flask_wtf import FlaskForm
from wtforms import SubmitField
from flask_wtf.file import FileField, FileRequired, FileAllowed


class UploadSyllabus(FlaskForm):
    syllabus = FileField('', validators=[FileRequired(), FileAllowed(['pdf', 'txt', 'docx'], '.PDF, .Txt and .Docx files only')])
    submit = SubmitField('Upload Course Syllabus (PDF) file')

