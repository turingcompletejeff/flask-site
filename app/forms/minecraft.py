"""
Forms for Minecraft command management (TC-50) and fast travel locations (TC-46).

Forms:
- DeleteMinecraftCommandForm: CSRF-protected delete confirmation
- MinecraftLocationForm: Create/edit fast travel locations with coordinate validation
"""

from typing import Optional
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, SubmitField
from wtforms.validators import DataRequired, InputRequired, ValidationError, Optional as OptionalValidator


class DeleteMinecraftCommandForm(FlaskForm):
    """
    CSRF-protected form for command deletion.

    Used in delete modal to ensure CSRF protection on DELETE operations.
    Does not require any input fields besides the submit button.
    """
    submit = SubmitField('Delete Command')


class MinecraftLocationForm(FlaskForm):
    """
    Form for creating and editing Minecraft fast travel locations.

    Includes custom validators for Minecraft coordinate bounds:
    - X/Z: -30,000,000 to 30,000,000 (world border)
    - Y: -64 to 320 (Minecraft 1.18+ build limits)
    """
    name = StringField(
        'Location Name',
        validators=[DataRequired(message='Location name is required')]
    )

    description = TextAreaField(
        'Description',
        validators=[OptionalValidator()]
    )

    position_x = FloatField(
        'X Coordinate',
        validators=[InputRequired(message='X coordinate is required')]
    )

    position_y = FloatField(
        'Y Coordinate',
        validators=[InputRequired(message='Y coordinate is required')]
    )

    position_z = FloatField(
        'Z Coordinate',
        validators=[InputRequired(message='Z coordinate is required')]
    )

    portrait = FileField(
        'Portrait Image',
        validators=[
            OptionalValidator(),
            FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPG and PNG images are allowed')
        ]
    )

    thumbnail = FileField(
        'Custom Thumbnail (Optional)',
        validators=[
            OptionalValidator(),
            FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPG and PNG images are allowed')
        ]
    )

    submit = SubmitField('Save Location')

    def validate_position_x(self, field: FloatField) -> None:
        """
        Validate X coordinate is within Minecraft world bounds.

        Args:
            field: The FloatField containing the X coordinate

        Raises:
            ValidationError: If X coordinate is outside [-30,000,000, 30,000,000]
        """
        if field.data is not None:
            if not (-30_000_000 <= field.data <= 30_000_000):
                raise ValidationError(
                    'X coordinate must be between -30,000,000 and 30,000,000'
                )

    def validate_position_y(self, field: FloatField) -> None:
        """
        Validate Y coordinate is within Minecraft world bounds.

        Args:
            field: The FloatField containing the Y coordinate

        Raises:
            ValidationError: If Y coordinate is outside [-64, 320] (Minecraft 1.18+)
        """
        if field.data is not None:
            if not (-64 <= field.data <= 320):
                raise ValidationError(
                    'Y coordinate must be between -64 and 320'
                )

    def validate_position_z(self, field: FloatField) -> None:
        """
        Validate Z coordinate is within Minecraft world bounds.

        Args:
            field: The FloatField containing the Z coordinate

        Raises:
            ValidationError: If Z coordinate is outside [-30,000,000, 30,000,000]
        """
        if field.data is not None:
            if not (-30_000_000 <= field.data <= 30_000_000):
                raise ValidationError(
                    'Z coordinate must be between -30,000,000 and 30,000,000'
                )
