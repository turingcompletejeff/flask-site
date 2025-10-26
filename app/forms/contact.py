from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError, Optional, NoneOf
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
            ('', 'reason for contact'),
            ('informational','informational'),
            ('personal','personal'),
            ('hiring','hiring / recruitment'),
            ('other','other')
        ],
        validators=[
            DataRequired(message='Please select a reason for contact.'),
            NoneOf([''], message='Please select a valid reason.')
        ]
    )
    other_reason = StringField(
        "please specify",
        render_kw={
            'placeholder': 'Please describe your reason for contacting us',
            'maxlength': 200
        }
    )
    message = TextAreaField("message", validators=[DataRequired()])
    submit = SubmitField("send")

    def validate_other_reason(self, field):
        """Custom validator: other_reason is required when reason='other', optional otherwise."""
        if self.reason.data == 'other':
            # When reason is 'other', other_reason is required
            if not field.data or not field.data.strip():
                raise ValidationError('Please specify your reason when selecting "Other".')
            if len(field.data.strip()) < 4:
                raise ValidationError('Please provide a more detailed reason (at least 4 characters).')
        # When reason is not 'other', other_reason can be empty (no validation needed)
