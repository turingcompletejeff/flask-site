from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, PasswordField, EmailField, SelectMultipleField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Email, ValidationError, Length, EqualTo, Optional
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
    save_draft = SubmitField("Save Draft")
    publish = SubmitField("Publish")

class ProfileEditForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    submit = SubmitField('Update Profile')

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    roles = SelectMultipleField('Roles', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Changes')

class CreateUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Create User')

class DeleteUserForm(FlaskForm):
    submit = SubmitField('Delete User')
