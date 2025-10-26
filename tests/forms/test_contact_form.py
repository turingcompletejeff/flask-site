"""
Comprehensive test suite for app/forms/contact.py

Tests coverage:
- PhoneNumber validator (11 tests): Valid formats, invalid formats, empty field
- ContactForm field validation (8 tests): Required fields, email format, reason dropdown
- ContactForm other_reason custom validation (11 tests): Conditional required field logic
- Successful form submissions (5 tests): Full valid form with different field combinations

Total: 35 tests targeting 95%+ code coverage of 62 lines.

Test organization:
1. TestPhoneNumberValidator - Tests the custom PhoneNumber validator class
2. TestContactFormFields - Tests individual form field validators
3. TestContactFormOtherReasonValidation - Tests the custom validate_other_reason method
4. TestContactFormSubmissions - Tests complete valid form submissions

Uses AAA pattern (Arrange-Act-Assert) throughout.
"""

import pytest
from wtforms import ValidationError
from app.forms.contact import PhoneNumber, ContactForm


class TestPhoneNumberValidator:
    """Test suite for the PhoneNumber custom validator.

    Tests both valid and invalid phone number formats, custom error messages,
    and the optional field behavior (empty field should pass validation).
    """

    def test_phone_valid_10_digits_no_formatting(self, app):
        """Test valid 10-digit phone number without any formatting."""
        # Arrange
        validator = PhoneNumber()

        with app.test_request_context():
            form = ContactForm()
            form.phone.data = '1234567890'

            # Act & Assert - should not raise ValidationError
            try:
                validator(form, form.phone)
            except ValidationError:
                pytest.fail("Should accept valid 10-digit phone number")

    def test_phone_valid_with_parentheses_formatting(self, app):
        """Test valid phone number with (xxx) xxx-xxxx formatting."""
        # Arrange
        validator = PhoneNumber()

        with app.test_request_context():
            form = ContactForm()
            form.phone.data = '(123) 456-7890'

            # Act & Assert
            try:
                validator(form, form.phone)
            except ValidationError:
                pytest.fail("Should accept phone with (xxx) xxx-xxxx format")

    def test_phone_valid_with_hyphen_formatting(self, app):
        """Test valid phone number with xxx-xxx-xxxx formatting."""
        # Arrange
        validator = PhoneNumber()

        with app.test_request_context():
            form = ContactForm()
            form.phone.data = '123-456-7890'

            # Act & Assert
            try:
                validator(form, form.phone)
            except ValidationError:
                pytest.fail("Should accept phone with xxx-xxx-xxxx format")

    def test_phone_valid_with_dots_formatting(self, app):
        """Test valid phone number with xxx.xxx.xxxx formatting."""
        # Arrange
        validator = PhoneNumber()

        with app.test_request_context():
            form = ContactForm()
            form.phone.data = '123.456.7890'

            # Act & Assert
            try:
                validator(form, form.phone)
            except ValidationError:
                pytest.fail("Should accept phone with xxx.xxx.xxxx format")

    def test_phone_valid_with_spaces_formatting(self, app):
        """Test valid phone number with xxx xxx xxxx formatting (spaces)."""
        # Arrange
        validator = PhoneNumber()

        with app.test_request_context():
            form = ContactForm()
            form.phone.data = '123 456 7890'

            # Act & Assert
            try:
                validator(form, form.phone)
            except ValidationError:
                pytest.fail("Should accept phone with space formatting")

    def test_phone_empty_field_optional(self, app):
        """Test that empty phone number passes validation (optional field)."""
        # Arrange
        validator = PhoneNumber()

        with app.test_request_context():
            form = ContactForm()
            form.phone.data = ''

            # Act & Assert - empty field should not raise error
            try:
                validator(form, form.phone)
            except ValidationError:
                pytest.fail("Empty phone field should be valid (optional)")

    def test_phone_none_field_optional(self, app):
        """Test that None phone number passes validation (optional field)."""
        # Arrange
        validator = PhoneNumber()

        with app.test_request_context():
            form = ContactForm()
            form.phone.data = None

            # Act & Assert
            try:
                validator(form, form.phone)
            except ValidationError:
                pytest.fail("None phone field should be valid (optional)")

    def test_phone_invalid_less_than_10_digits(self, app):
        """Test that phone number with less than 10 digits raises error."""
        # Arrange
        validator = PhoneNumber()

        with app.test_request_context():
            form = ContactForm()
            form.phone.data = '12345678'  # 8 digits

            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                validator(form, form.phone)
            assert 'Invalid phone number format' in str(exc_info.value)

    def test_phone_invalid_more_than_10_digits(self, app):
        """Test that phone number with more than 10 digits raises error."""
        # Arrange
        validator = PhoneNumber()

        with app.test_request_context():
            form = ContactForm()
            form.phone.data = '12345678901'  # 11 digits

            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                validator(form, form.phone)
            assert 'Invalid phone number format' in str(exc_info.value)

    def test_phone_invalid_letters_mixed_with_numbers(self, app):
        """Test that phone with letters mixed in raises error."""
        # Arrange
        validator = PhoneNumber()

        with app.test_request_context():
            form = ContactForm()
            form.phone.data = '123ABC7890'

            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                validator(form, form.phone)
            assert 'Invalid phone number format' in str(exc_info.value)

    def test_phone_invalid_only_letters(self, app):
        """Test that phone with only letters raises error."""
        # Arrange
        validator = PhoneNumber()

        with app.test_request_context():
            form = ContactForm()
            form.phone.data = 'abcdefghij'

            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                validator(form, form.phone)
            assert 'Invalid phone number format' in str(exc_info.value)

    def test_phone_custom_error_message(self, app):
        """Test that custom error message is used when provided."""
        # Arrange
        custom_message = 'Phone number must be exactly 10 digits.'
        validator = PhoneNumber(message=custom_message)

        with app.test_request_context():
            form = ContactForm()
            form.phone.data = '123'

            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                validator(form, form.phone)
            assert custom_message in str(exc_info.value)


class TestContactFormFields:
    """Test suite for ContactForm field validators.

    Tests individual field requirements and validators, excluding the custom
    validate_other_reason logic which is tested separately.
    """

    def test_name_field_required(self, app):
        """Test that name field is required."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': '',
                'email': 'test@example.com',
                'phone': '',
                'reason': 'informational',
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert not is_valid
            assert 'name' in form.errors
            assert any('required' in str(error).lower() for error in form.errors['name'])

    def test_email_field_required(self, app):
        """Test that email field is required."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': '',
                'phone': '',
                'reason': 'informational',
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert not is_valid
            assert 'email' in form.errors

    def test_email_field_format_validation(self, app):
        """Test that email field validates email format."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'invalid-email',
                'phone': '',
                'reason': 'informational',
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert not is_valid
            assert 'email' in form.errors
            assert any('invalid' in str(error).lower() for error in form.errors['email'])

    def test_phone_field_optional(self, app):
        """Test that phone field is optional (can be empty)."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'test@example.com',
                'phone': '',
                'reason': 'informational',
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert is_valid or 'phone' not in form.errors

    def test_reason_field_required(self, app):
        """Test that reason field is required."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'test@example.com',
                'phone': '',
                'reason': '',
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert not is_valid
            assert 'reason' in form.errors

    def test_reason_field_empty_string_invalid(self, app):
        """Test that reason field cannot be empty string (DataRequired validator)."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'test@example.com',
                'phone': '',
                'reason': '',
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert not is_valid
            assert 'reason' in form.errors
            # DataRequired triggers first, so we get its message
            assert any('select a reason' in str(error).lower() for error in form.errors['reason'])

    def test_message_field_required(self, app):
        """Test that message field is required."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'test@example.com',
                'phone': '',
                'reason': 'informational',
                'message': ''
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert not is_valid
            assert 'message' in form.errors

    def test_reason_field_valid_choices(self, app):
        """Test that reason field accepts all valid choices."""
        # Arrange
        valid_reasons = ['informational', 'personal', 'hiring', 'other']

        # Act & Assert
        for reason in valid_reasons:
            with app.test_request_context():
                form = ContactForm(data={
                    'name': 'John Doe',
                    'email': 'test@example.com',
                    'phone': '',
                    'reason': reason,
                    'message': 'Test message'
                })

                # For 'other', we'll skip message validation to isolate this test
                if reason == 'other':
                    form.other_reason.data = 'Custom reason'

                is_valid = form.validate()

                # Reason itself should not have errors (other errors may exist for other_reason)
                assert 'reason' not in form.errors


class TestContactFormOtherReasonValidation:
    """Test suite for the custom validate_other_reason method.

    Tests the conditional logic that makes other_reason required and validated
    only when reason='other', and optional otherwise.
    """

    def test_other_reason_required_when_reason_is_other(self, app):
        """Test that other_reason is required when reason='other'."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'test@example.com',
                'phone': '',
                'reason': 'other',
                'other_reason': '',
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert not is_valid
            assert 'other_reason' in form.errors
            assert any('specify' in str(error).lower() for error in form.errors['other_reason'])

    def test_other_reason_cannot_be_empty_when_reason_is_other(self, app):
        """Test that other_reason cannot be just whitespace when reason='other'."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'test@example.com',
                'phone': '',
                'reason': 'other',
                'other_reason': '   ',  # Whitespace only
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert not is_valid
            assert 'other_reason' in form.errors

    def test_other_reason_minimum_length_when_reason_is_other(self, app):
        """Test that other_reason must be at least 4 characters when reason='other'."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'test@example.com',
                'phone': '',
                'reason': 'other',
                'other_reason': 'abc',  # Only 3 characters
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert not is_valid
            assert 'other_reason' in form.errors
            assert any('4 characters' in str(error).lower() for error in form.errors['other_reason'])

    def test_other_reason_exactly_4_characters_valid(self, app):
        """Test that other_reason with exactly 4 characters is valid when reason='other'."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'test@example.com',
                'phone': '',
                'reason': 'other',
                'other_reason': 'test',  # Exactly 4 characters
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert is_valid
            assert 'other_reason' not in form.errors

    def test_other_reason_optional_when_reason_is_not_other(self, app):
        """Test that other_reason is optional when reason is not 'other'."""
        # Arrange
        valid_reasons = ['informational', 'personal', 'hiring']

        # Act & Assert
        for reason in valid_reasons:
            with app.test_request_context():
                form = ContactForm(data={
                    'name': 'John Doe',
                    'email': 'test@example.com',
                    'phone': '',
                    'reason': reason,
                    'other_reason': '',  # Empty - should be fine
                    'message': 'Test message'
                })

                is_valid = form.validate()

                # other_reason should not have errors
                assert 'other_reason' not in form.errors

    def test_other_reason_can_be_ignored_when_reason_is_informational(self, app):
        """Test that other_reason is completely ignored when reason='informational'."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'test@example.com',
                'phone': '',
                'reason': 'informational',
                'other_reason': '',
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert is_valid
            assert 'other_reason' not in form.errors

    def test_other_reason_can_be_ignored_when_reason_is_personal(self, app):
        """Test that other_reason is completely ignored when reason='personal'."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'test@example.com',
                'phone': '',
                'reason': 'personal',
                'other_reason': '',
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert is_valid
            assert 'other_reason' not in form.errors

    def test_other_reason_can_be_ignored_when_reason_is_hiring(self, app):
        """Test that other_reason is completely ignored when reason='hiring'."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'test@example.com',
                'phone': '',
                'reason': 'hiring',
                'other_reason': '',
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert is_valid
            assert 'other_reason' not in form.errors

    def test_other_reason_long_valid_input_when_reason_is_other(self, app):
        """Test that other_reason accepts long detailed input when reason='other'."""
        # Arrange
        long_reason = 'This is a detailed explanation of why I am contacting you today.'

        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'test@example.com',
                'phone': '',
                'reason': 'other',
                'other_reason': long_reason,
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert is_valid
            assert 'other_reason' not in form.errors

    def test_other_reason_validates_after_strip(self, app):
        """Test that other_reason validation correctly uses stripped value for length check."""
        # Arrange - leading/trailing spaces that should be stripped
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'test@example.com',
                'phone': '',
                'reason': 'other',
                'other_reason': '  test  ',  # Should strip to 'test' (4 chars)
                'message': 'Test message'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert is_valid
            assert 'other_reason' not in form.errors


class TestContactFormSubmissions:
    """Test suite for complete valid ContactForm submissions.

    Tests successful form validation with different valid combinations
    of fields to ensure all code paths pass validation.
    """

    def test_valid_form_with_all_required_fields(self, app):
        """Test valid form submission with all required fields."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': '',
                'reason': 'informational',
                'other_reason': '',
                'message': 'I have a question about your services.'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert is_valid
            assert len(form.errors) == 0

    def test_valid_form_with_reason_informational(self, app):
        """Test valid form with reason='informational' (no other_reason needed)."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'phone': '',
                'reason': 'informational',
                'other_reason': '',
                'message': 'I would like more information about your products.'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert is_valid
            assert 'other_reason' not in form.errors

    def test_valid_form_with_reason_other_and_other_reason(self, app):
        """Test valid form with reason='other' and valid other_reason."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'Bob Johnson',
                'email': 'bob@example.com',
                'phone': '',
                'reason': 'other',
                'other_reason': 'Partnership opportunity in emerging markets',
                'message': 'I think we could work together on new initiatives.'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert is_valid
            assert 'other_reason' not in form.errors

    def test_valid_form_with_optional_phone_number(self, app):
        """Test valid form submission with optional phone number included."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'Alice Brown',
                'email': 'alice@example.com',
                'phone': '(555) 123-4567',
                'reason': 'personal',
                'other_reason': '',
                'message': 'I wanted to reach out personally.'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert is_valid
            assert 'phone' not in form.errors

    def test_valid_form_without_phone_number(self, app):
        """Test valid form submission without phone number."""
        # Arrange
        with app.test_request_context():
            form = ContactForm(data={
                'name': 'Charlie Davis',
                'email': 'charlie@example.com',
                'phone': '',
                'reason': 'hiring',
                'other_reason': '',
                'message': 'We are interested in hiring talented individuals.'
            })

            # Act
            is_valid = form.validate()

            # Assert
            assert is_valid
            assert 'phone' not in form.errors
