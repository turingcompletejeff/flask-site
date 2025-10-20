"""
Forms for Minecraft command management (TC-50).

Forms:
- DeleteMinecraftCommandForm: CSRF-protected delete confirmation
"""

from flask_wtf import FlaskForm
from wtforms import SubmitField


class DeleteMinecraftCommandForm(FlaskForm):
    """
    CSRF-protected form for command deletion.

    Used in delete modal to ensure CSRF protection on DELETE operations.
    Does not require any input fields besides the submit button.
    """
    submit = SubmitField('Delete Command')
