from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Email, ValidationError
import re

class PhoneNumber:
    def __init__(self, message=None):
        if not message:
            message = 'Invalid phone number format.'
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return

        phone = re.sub(r'[^\d]', '', field.data)

        if len(phone) != 10:
            raise ValidationError(self.message)

        if not re.match(r'^\d{10}$', phone):
            raise ValidationError(self.message)

class ContactForm(FlaskForm):
    name = StringField("name", validators=[DataRequired()])
    email = StringField("email", validators=[DataRequired(), Email()])
    phone = StringField("phone number", validators=[PhoneNumber()])
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
