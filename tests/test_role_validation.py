import pytest
from app.models.user import Role

def test_default_badge_color():
    """Test default badge color is #58cc02."""
    role = Role(name='test_role', description='Test role')
    assert role.badge_color == '#58cc02'

def test_validate_hex_color_valid_formats():
    """Test various valid hex color formats."""
    valid_colors = [
        '#fff',    # 3 digit shorthand
        '#FFF',    # Uppercase
        '#ffffff', # 6 digit full
        '#ABCDEF', # Mixed case
        '#123456'  # Darker colors
    ]
    for color in valid_colors:
        assert Role.validate_hex_color(color) == True, f"Color {color} should be valid"

def test_validate_hex_color_invalid_formats():
    """Test invalid hex color formats."""
    invalid_colors = [
        '#ggg',      # Invalid characters
        '#12345',    # Incorrect length
        '#1234567',  # Too long
        'rgb(255, 0, 0)', # Not a hex color
        '#',         # Just a hash
        '',          # Empty string
        None         # None value
    ]
    for color in invalid_colors:
        assert Role.validate_hex_color(color) == False, f"Color {color} should be invalid"

def test_create_role_with_custom_badge_color():
    """Test creating a role with a custom badge color."""
    custom_color = '#FF0000'
    role = Role(name='custom_badge', description='Custom Badge Color', badge_color=custom_color)
    assert role.badge_color == custom_color
    assert Role.validate_hex_color(role.badge_color) == True

def test_update_role_badge_color():
    """Test updating a role's badge color."""
    role = Role(name='update_color_test', description='Update color test')
    assert role.badge_color == '#58cc02'  # Default color

    role.badge_color = '#00FF00'  # Update color
    assert role.badge_color == '#00FF00'
    assert Role.validate_hex_color(role.badge_color) == True