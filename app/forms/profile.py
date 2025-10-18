from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, TextAreaField, EmailField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Email, Length, EqualTo


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
