from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
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
            ('hiring','hiring / recruitment'),
            ('other','other')
        ],
        validators=[DataRequired()]
    )
    message = TextAreaField("message", validators=[DataRequired()])
    submit = SubmitField("send")
