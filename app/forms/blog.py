from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired


class BlogPostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    content = TextAreaField("Content", validators=[DataRequired()])
    portrait = FileField("Portrait", validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    thumbnail = FileField("Custom Thumbnail (Optional)", validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    save_draft = SubmitField("Save Draft")
    publish = SubmitField("Publish")
