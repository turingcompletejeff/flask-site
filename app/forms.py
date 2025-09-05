from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired

class BlogPostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    content = TextAreaField("Content", validators=[DataRequired()])
    portrait = FileField("Portrait", validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField("Post")
