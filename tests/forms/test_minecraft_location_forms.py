"""
Comprehensive test suite for MinecraftLocationForm.

Tests coverage:
- Field validation: Required fields (name, coordinates)
- Coordinate validators: Minecraft world bounds (x, y, z)
- Optional fields: Description, images
- File upload validation: Portrait and thumbnail
- Custom validators: validate_position_x, validate_position_y, validate_position_z

Total: 17 tests targeting coordinate validation and form field requirements.

Test organization:
1. TestMinecraftLocationFormFields - Basic field validation
2. TestCoordinateValidators - Minecraft world bounds validation
3. TestImageFields - File upload validation
4. TestFormSubmissions - Complete valid form submissions
"""

import pytest
from wtforms import ValidationError
from werkzeug.datastructures import FileStorage
import io


@pytest.mark.unit
class TestMinecraftLocationFormFields:
    """Test suite for basic form field validation."""

    def test_form_requires_name(self, app):
        """Test that name field is required."""
        from app.forms.minecraft import MinecraftLocationForm

        with app.test_request_context():
            form = MinecraftLocationForm(
                name='',
                position_x=0.0,
                position_y=64.0,
                position_z=0.0
            )
            assert not form.validate()
            assert 'name' in form.errors

    def test_form_requires_position_x(self, app):
        """Test that position_x field is required."""
        from app.forms.minecraft import MinecraftLocationForm

        with app.test_request_context():
            form = MinecraftLocationForm(
                name='Test Location',
                position_x=None,
                position_y=64.0,
                position_z=0.0
            )
            assert not form.validate()
            assert 'position_x' in form.errors

    def test_form_requires_position_y(self, app):
        """Test that position_y field is required."""
        from app.forms.minecraft import MinecraftLocationForm

        with app.test_request_context():
            form = MinecraftLocationForm(
                name='Test Location',
                position_x=0.0,
                position_y=None,
                position_z=0.0
            )
            assert not form.validate()
            assert 'position_y' in form.errors

    def test_form_requires_position_z(self, app):
        """Test that position_z field is required."""
        from app.forms.minecraft import MinecraftLocationForm

        with app.test_request_context():
            form = MinecraftLocationForm(
                name='Test Location',
                position_x=0.0,
                position_y=64.0,
                position_z=None
            )
            assert not form.validate()
            assert 'position_z' in form.errors

    def test_description_is_optional(self, app):
        """Test that description field is optional."""
        from app.forms.minecraft import MinecraftLocationForm

        with app.test_request_context():
            form = MinecraftLocationForm(
                name='Test Location',
                position_x=0.0,
                position_y=64.0,
                position_z=0.0,
                description=''
            )
            # Should validate even without description
            # Note: May fail due to coordinate validators, but description won't be in errors
            form.validate()
            assert 'description' not in form.errors


@pytest.mark.unit
class TestCoordinateValidators:
    """Test suite for Minecraft coordinate validation."""

    def test_position_x_within_bounds(self, app):
        """Test that valid X coordinates are accepted."""
        from app.forms.minecraft import MinecraftLocationForm
        from werkzeug.datastructures import MultiDict

        with app.test_request_context(method='POST'):
            form_data = MultiDict([
                ('name', 'Test Location'),
                ('position_x', '1000.0'),
                ('position_y', '64.0'),
                ('position_z', '0.0')
            ])
            form = MinecraftLocationForm(formdata=form_data)
            form.validate()
            assert 'position_x' not in form.errors

    def test_position_x_too_large(self, app):
        """Test that X coordinate exceeding max bound is rejected."""
        from app.forms.minecraft import MinecraftLocationForm
        from werkzeug.datastructures import MultiDict

        with app.test_request_context(method='POST'):
            form_data = MultiDict([
                ('name', 'Test Location'),
                ('position_x', '30000001.0'),  # Exceeds max of 30,000,000
                ('position_y', '64.0'),
                ('position_z', '0.0')
            ])
            form = MinecraftLocationForm(formdata=form_data)
            assert not form.validate()
            assert 'position_x' in form.errors

    def test_position_x_too_small(self, app):
        """Test that X coordinate below min bound is rejected."""
        from app.forms.minecraft import MinecraftLocationForm
        from werkzeug.datastructures import MultiDict

        with app.test_request_context(method='POST'):
            form_data = MultiDict([
                ('name', 'Test Location'),
                ('position_x', '-30000001.0'),  # Below min of -30,000,000
                ('position_y', '64.0'),
                ('position_z', '0.0')
            ])
            form = MinecraftLocationForm(formdata=form_data)
            assert not form.validate()
            assert 'position_x' in form.errors

    def test_position_y_within_bounds(self, app):
        """Test that valid Y coordinates are accepted."""
        from app.forms.minecraft import MinecraftLocationForm
        from werkzeug.datastructures import MultiDict

        with app.test_request_context(method='POST'):
            form_data = MultiDict([
                ('name', 'Test Location'),
                ('position_x', '0.0'),
                ('position_y', '100.0'),
                ('position_z', '0.0')
            ])
            form = MinecraftLocationForm(formdata=form_data)
            form.validate()
            assert 'position_y' not in form.errors

    def test_position_y_too_high(self, app):
        """Test that Y coordinate above build limit is rejected."""
        from app.forms.minecraft import MinecraftLocationForm
        from werkzeug.datastructures import MultiDict

        with app.test_request_context(method='POST'):
            form_data = MultiDict([
                ('name', 'Test Location'),
                ('position_x', '0.0'),
                ('position_y', '321.0'),  # Exceeds max of 320
                ('position_z', '0.0')
            ])
            form = MinecraftLocationForm(formdata=form_data)
            assert not form.validate()
            assert 'position_y' in form.errors

    def test_position_y_too_low(self, app):
        """Test that Y coordinate below void is rejected."""
        from app.forms.minecraft import MinecraftLocationForm
        from werkzeug.datastructures import MultiDict

        with app.test_request_context(method='POST'):
            form_data = MultiDict([
                ('name', 'Test Location'),
                ('position_x', '0.0'),
                ('position_y', '-65.0'),  # Below min of -64
                ('position_z', '0.0')
            ])
            form = MinecraftLocationForm(formdata=form_data)
            assert not form.validate()
            assert 'position_y' in form.errors

    def test_position_z_within_bounds(self, app):
        """Test that valid Z coordinates are accepted."""
        from app.forms.minecraft import MinecraftLocationForm
        from werkzeug.datastructures import MultiDict

        with app.test_request_context(method='POST'):
            form_data = MultiDict([
                ('name', 'Test Location'),
                ('position_x', '0.0'),
                ('position_y', '64.0'),
                ('position_z', '-5000.0')
            ])
            form = MinecraftLocationForm(formdata=form_data)
            form.validate()
            assert 'position_z' not in form.errors

    def test_position_z_too_large(self, app):
        """Test that Z coordinate exceeding max bound is rejected."""
        from app.forms.minecraft import MinecraftLocationForm
        from werkzeug.datastructures import MultiDict

        with app.test_request_context(method='POST'):
            form_data = MultiDict([
                ('name', 'Test Location'),
                ('position_x', '0.0'),
                ('position_y', '64.0'),
                ('position_z', '30000001.0')  # Exceeds max of 30,000,000
            ])
            form = MinecraftLocationForm(formdata=form_data)
            assert not form.validate()
            assert 'position_z' in form.errors

    def test_position_z_too_small(self, app):
        """Test that Z coordinate below min bound is rejected."""
        from app.forms.minecraft import MinecraftLocationForm
        from werkzeug.datastructures import MultiDict

        with app.test_request_context(method='POST'):
            form_data = MultiDict([
                ('name', 'Test Location'),
                ('position_x', '0.0'),
                ('position_y', '64.0'),
                ('position_z', '-30000001.0')  # Below min of -30,000,000
            ])
            form = MinecraftLocationForm(formdata=form_data)
            assert not form.validate()
            assert 'position_z' in form.errors


@pytest.mark.unit
class TestImageFields:
    """Test suite for image upload fields."""

    def test_portrait_field_accepts_jpg(self, app, mock_image_file):
        """Test that portrait field accepts JPG files."""
        from app.forms.minecraft import MinecraftLocationForm

        with app.test_request_context():
            form = MinecraftLocationForm(
                name='Test Location',
                position_x=0.0,
                position_y=64.0,
                position_z=0.0,
                portrait=mock_image_file
            )
            # Portrait validation should not fail for valid JPG
            form.validate()
            assert 'portrait' not in form.errors

    def test_thumbnail_is_optional(self, app):
        """Test that thumbnail field is optional."""
        from app.forms.minecraft import MinecraftLocationForm

        with app.test_request_context():
            form = MinecraftLocationForm(
                name='Test Location',
                position_x=0.0,
                position_y=64.0,
                position_z=0.0
            )
            form.validate()
            assert 'thumbnail' not in form.errors


@pytest.mark.unit
class TestFormSubmissions:
    """Test suite for complete valid form submissions."""

    def test_valid_form_minimal_fields(self, app):
        """Test form with only required fields."""
        from app.forms.minecraft import MinecraftLocationForm
        from werkzeug.datastructures import MultiDict

        with app.test_request_context(method='POST'):
            form_data = MultiDict([
                ('name', 'Spawn Point'),
                ('position_x', '0.0'),
                ('position_y', '64.0'),
                ('position_z', '0.0')
            ])
            form = MinecraftLocationForm(formdata=form_data)
            is_valid = form.validate()
            if not is_valid:
                print(f"Form errors: {form.errors}")
            assert is_valid

    def test_valid_form_with_description(self, app):
        """Test form with description field."""
        from app.forms.minecraft import MinecraftLocationForm
        from werkzeug.datastructures import MultiDict

        with app.test_request_context(method='POST'):
            form_data = MultiDict([
                ('name', 'Castle'),
                ('description', 'Main player castle'),
                ('position_x', '500.0'),
                ('position_y', '80.0'),
                ('position_z', '-300.0')
            ])
            form = MinecraftLocationForm(formdata=form_data)
            assert form.validate()
