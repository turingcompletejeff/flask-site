from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Email

class ContactForm(FlaskForm):
    name = StringField("name", validators=[DataRequired()])
    email = StringField("email", validators=[DataRequired(), Email()])
    reason = SelectField(
        "reason for contact",
        choices=[
            ('informational','informational'),
            ('personal','personal'),
            ('hiring / recruitment','hiring'),
            ('other','other')
        ],
        validators=[DataRequired()]
    )
    message = TextAreaField("message", validators=[DataRequired()])
    submit = SubmitField("send")

class BlogPostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    content = TextAreaField("Content", validators=[DataRequired()])
    portrait = FileField("Portrait", validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    thumbnail = FileField("Custom Thumbnail (Optional)", validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField("Post")
