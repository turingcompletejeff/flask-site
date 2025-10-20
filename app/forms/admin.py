from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, SelectMultipleField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
import re


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


def validate_hex_color(form, field):
    """Validate hex color code format (#RGB or #RRGGBB)"""
    if not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', field.data):
        raise ValidationError('Invalid hex color format. Use #RGB or #RRGGBB format (e.g., #58cc02)')


class CreateRoleForm(FlaskForm):
    name = StringField('Role Name', validators=[DataRequired(), Length(min=2, max=50)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=200)])
    badge_color = StringField('Badge Color', validators=[DataRequired(), validate_hex_color], default='#58cc02')
    submit = SubmitField('Create Role')


class EditRoleForm(FlaskForm):
    name = StringField('Role Name', validators=[DataRequired(), Length(min=2, max=50)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=200)])
    badge_color = StringField('Badge Color', validators=[DataRequired(), validate_hex_color], default='#58cc02')
    submit = SubmitField('Update Role')


class DeleteRoleForm(FlaskForm):
    submit = SubmitField('Delete Role')
