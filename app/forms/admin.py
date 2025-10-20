from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


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


class DeleteRoleForm(FlaskForm):
    submit = SubmitField('Delete Role')
