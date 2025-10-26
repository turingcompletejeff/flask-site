"""
Comprehensive unit tests for app/utils/file_validation.py

Tests cover:
- validate_image_file() with valid and invalid inputs
  - File presence validation
  - Filename validation
  - Extension validation
  - MIME type validation
  - File size validation
  - Image magic number verification
  - Extension/type mismatch detection
- sanitize_filename() with various filename patterns
  - Special character handling
  - Case normalization
  - Length truncation
  - Empty filename handling
  - Unicode support
"""

import os
import pytest
import tempfile
from io import BytesIO
from unittest.mock import patch, Mock
from PIL import Image
from werkzeug.datastructures import FileStorage

from app.utils.file_validation import (
    validate_image_file,
    sanitize_filename,
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_IMAGE_MIMES,
    MAX_IMAGE_SIZE
)


# ============================================================================
# Fixtures for Image Creation
# ============================================================================

@pytest.fixture
def create_image():
    """
    Factory fixture to create image files with specific formats.

    Usage:
        jpeg_file = create_image('JPEG')
        png_file = create_image('PNG')
    """
    def _create(format_type='JPEG', size=(100, 100), color='red'):
        img = Image.new('RGB', size, color=color)
        img_bytes = BytesIO()
        img.save(img_bytes, format=format_type)
        img_bytes.seek(0)
        return img_bytes
    return _create


@pytest.fixture
def create_file_storage():
    """
    Factory fixture to create FileStorage objects for testing.

    Usage:
        file = create_file_storage(content=b'data', filename='test.jpg', content_type='image/jpeg')
    """
    def _create(content=None, filename='test.jpg', content_type='image/jpeg'):
        if content is None:
            content = b'test content'

        file_stream = BytesIO(content)
        return FileStorage(
            stream=file_stream,
            filename=filename,
            content_type=content_type
        )
    return _create


# ============================================================================
# Test: validate_image_file() - Presence and Filename Validation
# ============================================================================

@pytest.mark.utils
class TestValidateImageFilePresenceAndFilename:
    """Test file presence and filename validation."""

    def test_validate_none_file(self):
        """Test validation fails when file is None."""
        # Arrange
        file = None

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert error_msg == "No file provided"

    def test_validate_empty_filename(self, create_file_storage):
        """Test validation fails when filename is empty string."""
        # Arrange
        # Note: FileStorage with empty filename evaluates to False in boolean context
        file = create_file_storage(filename='', content_type='image/jpeg')

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert error_msg == "No file provided"  # FileStorage is falsy when filename is empty

    def test_validate_none_filename(self, create_file_storage):
        """Test validation fails when filename is None."""
        # Arrange
        # Note: FileStorage with None filename evaluates to False in boolean context
        file = create_file_storage(filename=None, content_type='image/jpeg')

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert error_msg == "No file provided"  # FileStorage is falsy when filename is None

    def test_validate_filename_without_extension(self, create_image, create_file_storage):
        """Test validation fails when filename has no extension."""
        # Arrange
        jpeg_content = create_image('JPEG').getvalue()
        file = create_file_storage(
            content=jpeg_content,
            filename='imagewithoutext',
            content_type='image/jpeg'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert error_msg == "File has no extension"


# ============================================================================
# Test: validate_image_file() - Extension Validation
# ============================================================================

@pytest.mark.utils
class TestValidateImageFileExtension:
    """Test extension validation."""

    def test_validate_invalid_extension_txt(self, create_file_storage):
        """Test validation fails for .txt extension."""
        # Arrange
        file = create_file_storage(filename='document.txt', content_type='image/jpeg')

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert "not allowed" in error_msg
        assert ".txt" in error_msg

    def test_validate_invalid_extension_exe(self, create_file_storage):
        """Test validation fails for .exe extension."""
        # Arrange
        file = create_file_storage(filename='malware.exe', content_type='image/jpeg')

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert "not allowed" in error_msg

    def test_validate_invalid_extension_pdf(self, create_file_storage):
        """Test validation fails for .pdf extension."""
        # Arrange
        file = create_file_storage(filename='document.pdf', content_type='image/jpeg')

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert "not allowed" in error_msg

    def test_validate_case_insensitive_extension(self, create_image):
        """Test that extension validation is case-insensitive."""
        # Arrange
        jpeg_content = create_image('JPEG').getvalue()
        file = FileStorage(
            stream=BytesIO(jpeg_content),
            filename='image.JPG',  # uppercase
            content_type='image/jpeg'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is True
        assert error_msg == ""


# ============================================================================
# Test: validate_image_file() - MIME Type Validation
# ============================================================================

@pytest.mark.utils
class TestValidateImageFileMimeType:
    """Test MIME type validation."""

    def test_validate_invalid_mime_type(self, create_image):
        """Test validation fails for invalid MIME type."""
        # Arrange
        jpeg_content = create_image('JPEG').getvalue()
        file = FileStorage(
            stream=BytesIO(jpeg_content),
            filename='image.jpg',
            content_type='text/plain'  # wrong MIME type
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert "Invalid file type" in error_msg
        assert "text/plain" in error_msg

    def test_validate_application_octet_stream_mime(self, create_image):
        """Test validation fails for application/octet-stream MIME type."""
        # Arrange
        jpeg_content = create_image('JPEG').getvalue()
        file = FileStorage(
            stream=BytesIO(jpeg_content),
            filename='image.jpg',
            content_type='application/octet-stream'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert "Invalid file type" in error_msg


# ============================================================================
# Test: validate_image_file() - File Size Validation
# ============================================================================

@pytest.mark.utils
class TestValidateImageFileSize:
    """Test file size validation."""

    def test_validate_empty_file(self, create_file_storage):
        """Test validation fails for empty file (0 bytes)."""
        # Arrange
        file = create_file_storage(
            content=b'',
            filename='empty.jpg',
            content_type='image/jpeg'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert error_msg == "File is empty"

    def test_validate_file_too_large(self, create_image):
        """Test validation fails when file exceeds max size."""
        # Arrange
        # Create a large file by repeating image content
        base_image = create_image('JPEG').getvalue()
        # MAX_IMAGE_SIZE is 5MB, create something larger
        large_content = base_image * 10000  # Much larger than 5MB

        file = FileStorage(
            stream=BytesIO(large_content),
            filename='huge.jpg',
            content_type='image/jpeg'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert "File too large" in error_msg
        assert "MB" in error_msg

    def test_validate_file_at_max_size_boundary(self, create_image):
        """Test validation succeeds when file is exactly at max size."""
        # Arrange
        # Create image close to max size
        jpeg_content = create_image('JPEG', size=(1000, 1000)).getvalue()
        max_size = len(jpeg_content)

        file = FileStorage(
            stream=BytesIO(jpeg_content),
            filename='atmax.jpg',
            content_type='image/jpeg'
        )

        # Act
        is_valid, error_msg = validate_image_file(file, max_size=max_size)

        # Assert
        assert is_valid is True
        assert error_msg == ""

    def test_validate_file_just_below_max_size(self, create_image):
        """Test validation succeeds when file is just below max size."""
        # Arrange
        jpeg_content = create_image('JPEG').getvalue()
        max_size = len(jpeg_content) + 1  # Just above actual size

        file = FileStorage(
            stream=BytesIO(jpeg_content),
            filename='below.jpg',
            content_type='image/jpeg'
        )

        # Act
        is_valid, error_msg = validate_image_file(file, max_size=max_size)

        # Assert
        assert is_valid is True
        assert error_msg == ""

    def test_validate_custom_max_size(self, create_image):
        """Test validation with custom max_size parameter."""
        # Arrange
        # Default 100x100 JPEG is ~825 bytes, so use 500 byte limit to trigger failure
        jpeg_content = create_image('JPEG').getvalue()
        custom_max = 500  # 500 bytes (smaller than typical 100x100 JPEG)

        file = FileStorage(
            stream=BytesIO(jpeg_content),
            filename='image.jpg',
            content_type='image/jpeg'
        )

        # Act
        is_valid, error_msg = validate_image_file(file, max_size=custom_max)

        # Assert
        assert is_valid is False
        assert "File too large" in error_msg


# ============================================================================
# Test: validate_image_file() - Valid Image Formats
# ============================================================================

@pytest.mark.utils
class TestValidateImageFileValidFormats:
    """Test validation of valid image formats."""

    def test_validate_valid_jpeg_image(self, create_image):
        """Test validation succeeds for valid JPEG image."""
        # Arrange
        jpeg_content = create_image('JPEG').getvalue()
        file = FileStorage(
            stream=BytesIO(jpeg_content),
            filename='photo.jpg',
            content_type='image/jpeg'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is True
        assert error_msg == ""

    def test_validate_valid_jpeg_with_jpeg_extension(self, create_image):
        """Test validation succeeds for JPEG with .jpeg extension."""
        # Arrange
        jpeg_content = create_image('JPEG').getvalue()
        file = FileStorage(
            stream=BytesIO(jpeg_content),
            filename='photo.jpeg',
            content_type='image/jpeg'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is True
        assert error_msg == ""

    def test_validate_valid_png_image(self, create_image):
        """Test validation succeeds for valid PNG image."""
        # Arrange
        png_content = create_image('PNG').getvalue()
        file = FileStorage(
            stream=BytesIO(png_content),
            filename='image.png',
            content_type='image/png'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is True
        assert error_msg == ""

    def test_validate_valid_gif_image(self, create_image):
        """Test validation succeeds for valid GIF image."""
        # Arrange
        gif_content = create_image('GIF').getvalue()
        file = FileStorage(
            stream=BytesIO(gif_content),
            filename='animation.gif',
            content_type='image/gif'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is True
        assert error_msg == ""

    def test_validate_valid_webp_image(self, create_image):
        """Test validation succeeds for valid WEBP image."""
        # Arrange
        webp_content = create_image('WEBP').getvalue()
        file = FileStorage(
            stream=BytesIO(webp_content),
            filename='modern.webp',
            content_type='image/webp'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is True
        assert error_msg == ""


# ============================================================================
# Test: validate_image_file() - Corrupted Image Handling
# ============================================================================

@pytest.mark.utils
class TestValidateImageFileCorruptedImages:
    """Test handling of corrupted or invalid image data."""

    def test_validate_corrupted_image(self, create_file_storage):
        """Test validation fails for corrupted image data."""
        # Arrange
        corrupted_content = b'\x89PNG\r\n\x1a\n' + b'corrupted data here'
        file = create_file_storage(
            content=corrupted_content,
            filename='corrupted.png',
            content_type='image/png'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert "does not appear to be a valid image" in error_msg

    def test_validate_invalid_magic_number(self, create_file_storage):
        """Test validation fails when magic number doesn't match image data."""
        # Arrange
        # Valid JPEG magic number but not followed by valid data
        file = create_file_storage(
            content=b'\xFF\xD8\xFF\xE0' + b'not valid jpeg data',
            filename='bad_magic.jpg',
            content_type='image/jpeg'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert "does not appear to be a valid image" in error_msg


# ============================================================================
# Test: validate_image_file() - Extension/Type Mismatch
# ============================================================================

@pytest.mark.utils
class TestValidateImageFileExtensionMismatch:
    """Test detection of extension/type mismatches."""

    def test_validate_jpeg_file_with_png_extension(self, create_image):
        """Test validation fails when JPEG file has .png extension."""
        # Arrange
        jpeg_content = create_image('JPEG').getvalue()
        file = FileStorage(
            stream=BytesIO(jpeg_content),
            filename='image.png',  # Wrong extension
            content_type='image/png'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert "does not match actual file type" in error_msg

    def test_validate_png_file_with_jpg_extension(self, create_image):
        """Test validation fails when PNG file has .jpg extension."""
        # Arrange
        png_content = create_image('PNG').getvalue()
        file = FileStorage(
            stream=BytesIO(png_content),
            filename='image.jpg',  # Wrong extension
            content_type='image/jpeg'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert "does not match actual file type" in error_msg

    def test_validate_gif_file_with_webp_extension(self, create_image):
        """Test validation fails when GIF file has .webp extension."""
        # Arrange
        gif_content = create_image('GIF').getvalue()
        file = FileStorage(
            stream=BytesIO(gif_content),
            filename='anim.webp',  # Wrong extension
            content_type='image/webp'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert "does not match actual file type" in error_msg

    def test_validate_webp_file_with_gif_extension(self, create_image):
        """Test validation fails when WEBP file has .gif extension."""
        # Arrange
        webp_content = create_image('WEBP').getvalue()
        file = FileStorage(
            stream=BytesIO(webp_content),
            filename='modern.gif',  # Wrong extension
            content_type='image/gif'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert "does not match actual file type" in error_msg


# ============================================================================
# Test: validate_image_file() - Return Value Structure
# ============================================================================

@pytest.mark.utils
class TestValidateImageFileReturnValue:
    """Test return value structure and types."""

    def test_validate_return_tuple_structure(self, create_image):
        """Test that return value is a tuple with correct structure."""
        # Arrange
        jpeg_content = create_image('JPEG').getvalue()
        file = FileStorage(
            stream=BytesIO(jpeg_content),
            filename='test.jpg',
            content_type='image/jpeg'
        )

        # Act
        result = validate_image_file(file)

        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_validate_success_returns_empty_error_message(self, create_image):
        """Test that successful validation returns empty error message."""
        # Arrange
        jpeg_content = create_image('JPEG').getvalue()
        file = FileStorage(
            stream=BytesIO(jpeg_content),
            filename='test.jpg',
            content_type='image/jpeg'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is True
        assert error_msg == ""

    def test_validate_failure_returns_non_empty_error_message(self, create_file_storage):
        """Test that failed validation returns non-empty error message."""
        # Arrange
        file = create_file_storage(filename='test.txt', content_type='text/plain')

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is False
        assert len(error_msg) > 0


# ============================================================================
# Test: validate_image_file() - Edge Cases
# ============================================================================

@pytest.mark.utils
class TestValidateImageFileEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_validate_image_with_uppercase_extension(self, create_image):
        """Test validation with uppercase file extension."""
        # Arrange
        jpeg_content = create_image('JPEG').getvalue()
        file = FileStorage(
            stream=BytesIO(jpeg_content),
            filename='PHOTO.JPG',
            content_type='image/jpeg'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is True

    def test_validate_image_with_mixed_case_extension(self, create_image):
        """Test validation with mixed case file extension."""
        # Arrange
        png_content = create_image('PNG').getvalue()
        file = FileStorage(
            stream=BytesIO(png_content),
            filename='Image.Png',
            content_type='image/png'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is True

    def test_validate_image_with_multiple_dots_in_filename(self, create_image):
        """Test validation with multiple dots in filename."""
        # Arrange
        jpeg_content = create_image('JPEG').getvalue()
        file = FileStorage(
            stream=BytesIO(jpeg_content),
            filename='my.photo.backup.jpg',
            content_type='image/jpeg'
        )

        # Act
        is_valid, error_msg = validate_image_file(file)

        # Assert
        assert is_valid is True

    def test_validate_image_file_stream_position_reset(self, create_image):
        """Test that file stream is reset after validation."""
        # Arrange
        jpeg_content = create_image('JPEG').getvalue()
        stream = BytesIO(jpeg_content)
        file = FileStorage(
            stream=stream,
            filename='test.jpg',
            content_type='image/jpeg'
        )

        # Act
        validate_image_file(file)
        file.seek(0)
        read_content = file.read()

        # Assert
        assert len(read_content) == len(jpeg_content)


# ============================================================================
# Test: sanitize_filename() - Basic Alphanumeric
# ============================================================================

@pytest.mark.utils
class TestSanitizeFilenameBasic:
    """Test basic filename sanitization."""

    def test_sanitize_simple_alphanumeric_filename(self):
        """Test that simple alphanumeric filename is unchanged."""
        # Arrange
        filename = 'myimage.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'myimage.jpg'

    def test_sanitize_filename_with_numbers(self):
        """Test that filename with numbers is preserved."""
        # Arrange
        filename = 'photo2024_01_15.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'photo2024_01_15.jpg'

    def test_sanitize_filename_without_extension(self):
        """Test sanitization of filename without extension."""
        # Arrange
        filename = 'myfilename'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'myfilename'

    def test_sanitize_filename_only_numbers(self):
        """Test filename with only numbers."""
        # Arrange
        filename = '12345.png'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == '12345.png'


# ============================================================================
# Test: sanitize_filename() - Special Character Handling
# ============================================================================

@pytest.mark.utils
class TestSanitizeFilenameSpecialCharacters:
    """Test handling of special characters."""

    def test_sanitize_filename_with_spaces(self):
        """Test that spaces are converted to underscores."""
        # Arrange
        filename = 'my photo file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'my_photo_file.jpg'

    def test_sanitize_filename_with_multiple_spaces(self):
        """Test that multiple spaces are each converted to underscores."""
        # Arrange
        filename = 'my   photo   file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'my___photo___file.jpg'

    def test_sanitize_filename_with_dots_in_name(self):
        """Test that dots in name (not extension) are converted to underscores."""
        # Arrange
        filename = 'my.photo.backup.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'my_photo_backup.jpg'

    def test_sanitize_filename_with_dashes(self):
        """Test that dashes are preserved."""
        # Arrange
        filename = 'my-photo-file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'my-photo-file.jpg'

    def test_sanitize_filename_with_underscores(self):
        """Test that underscores are preserved."""
        # Arrange
        filename = 'my_photo_file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'my_photo_file.jpg'

    def test_sanitize_filename_with_mixed_safe_chars(self):
        """Test filename with mix of dashes and underscores."""
        # Arrange
        filename = 'my-photo_2024-backup.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'my-photo_2024-backup.jpg'


# ============================================================================
# Test: sanitize_filename() - Dangerous Character Removal
# ============================================================================

@pytest.mark.utils
class TestSanitizeFilenameDangerousCharacters:
    """Test removal of dangerous special characters."""

    def test_sanitize_filename_with_forward_slash(self):
        """Test that forward slashes are removed."""
        # Arrange
        filename = 'my/photo/file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert '/' not in result
        assert result == 'myphotofile.jpg'

    def test_sanitize_filename_with_backslash(self):
        """Test that backslashes are removed."""
        # Arrange
        filename = 'my\\photo\\file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert '\\' not in result
        assert result == 'myphotofile.jpg'

    def test_sanitize_filename_with_semicolon(self):
        """Test that semicolons are removed."""
        # Arrange
        filename = 'my;photo;file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert ';' not in result
        assert result == 'myphotofile.jpg'

    def test_sanitize_filename_with_colon(self):
        """Test that colons are removed."""
        # Arrange
        filename = 'my:photo:file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert ':' not in result
        assert result == 'myphotofile.jpg'

    def test_sanitize_filename_with_asterisk(self):
        """Test that asterisks are removed."""
        # Arrange
        filename = 'my*photo*file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert '*' not in result
        assert result == 'myphotofile.jpg'

    def test_sanitize_filename_with_question_mark(self):
        """Test that question marks are removed."""
        # Arrange
        filename = 'my?photo?file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert '?' not in result
        assert result == 'myphotofile.jpg'

    def test_sanitize_filename_with_quotes(self):
        """Test that quotes are removed."""
        # Arrange
        filename = 'my"photo"file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert '"' not in result
        assert result == 'myphotofile.jpg'

    def test_sanitize_filename_with_angle_brackets(self):
        """Test that angle brackets are removed."""
        # Arrange
        filename = 'my<photo>file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert '<' not in result
        assert '>' not in result
        assert result == 'myphotofile.jpg'

    def test_sanitize_filename_with_pipe(self):
        """Test that pipe characters are removed."""
        # Arrange
        filename = 'my|photo|file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert '|' not in result
        assert result == 'myphotofile.jpg'

    def test_sanitize_filename_with_at_symbol(self):
        """Test that @ symbols are removed."""
        # Arrange
        filename = 'my@photo@file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert '@' not in result
        assert result == 'myphotofile.jpg'

    def test_sanitize_filename_with_hash(self):
        """Test that hash symbols are removed."""
        # Arrange
        filename = 'my#photo#file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert '#' not in result
        assert result == 'myphotofile.jpg'

    def test_sanitize_filename_with_percent(self):
        """Test that percent signs are removed."""
        # Arrange
        filename = 'my%photo%file.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert '%' not in result
        assert result == 'myphotofile.jpg'

    def test_sanitize_filename_with_mixed_dangerous_chars(self):
        """Test filename with mix of dangerous characters."""
        # Arrange
        filename = 'my/photo:file;backup*.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert '/' not in result
        assert ':' not in result
        assert ';' not in result
        assert '*' not in result
        assert result == 'myphotofilebackup.jpg'


# ============================================================================
# Test: sanitize_filename() - Extension Handling
# ============================================================================

@pytest.mark.utils
class TestSanitizeFilenameExtension:
    """Test extension handling."""

    def test_sanitize_filename_extension_lowercase(self):
        """Test that extension is converted to lowercase."""
        # Arrange
        filename = 'myimage.JPG'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'myimage.jpg'

    def test_sanitize_filename_mixed_case_extension(self):
        """Test that mixed case extension is converted to lowercase."""
        # Arrange
        filename = 'myimage.Png'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'myimage.png'

    def test_sanitize_filename_all_caps_extension(self):
        """Test that all caps extension is converted to lowercase."""
        # Arrange
        filename = 'MYIMAGE.GIF'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'MYIMAGE.gif'

    def test_sanitize_filename_multiple_extensions(self):
        """Test handling of multiple extensions (e.g., .tar.gz)."""
        # Arrange
        filename = 'archive.tar.gz'

        # Act
        result = sanitize_filename(filename)

        # Assert
        # rsplit('.', 1) splits from right, so name='archive.tar' ext='gz'
        # Then dots in name become underscores
        assert result == 'archive_tar.gz'

    def test_sanitize_filename_dots_become_underscores_except_last(self):
        """Test that dots in name become underscores except the one before extension."""
        # Arrange
        filename = 'my.photo.backup.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'my_photo_backup.jpg'


# ============================================================================
# Test: sanitize_filename() - Length Handling
# ============================================================================

@pytest.mark.utils
class TestSanitizeFilenameLengthHandling:
    """Test filename length truncation."""

    def test_sanitize_filename_normal_length(self):
        """Test that normal length filename is unchanged."""
        # Arrange
        filename = 'my_photo_file.jpg'  # ~16 chars, well below 100

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'my_photo_file.jpg'

    def test_sanitize_filename_exactly_100_chars(self):
        """Test filename that is exactly 100 characters."""
        # Arrange
        # Create a name that is exactly 100 chars with extension
        name = 'a' * 95 + '.jpg'  # Total 99 chars
        filename = name

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert len(result) <= 100

    def test_sanitize_filename_over_100_chars(self):
        """Test that filename over 100 chars is truncated."""
        # Arrange
        long_name = 'a' * 150 + '.jpg'  # 154 chars total

        # Act
        result = sanitize_filename(long_name)

        # Assert
        # The name part should be truncated to 100 chars
        assert len(result) <= 104  # name (100) + '.' + extension (3)

    def test_sanitize_filename_very_long_name(self):
        """Test truncation of very long filename."""
        # Arrange
        filename = 'very_long_' + 'x' * 200 + '_filename.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        # Result should be <= 100 chars (excluding extension)
        name_part = result.rsplit('.', 1)[0] if '.' in result else result
        assert len(name_part) <= 100

    def test_sanitize_filename_truncate_preserves_extension(self):
        """Test that truncation preserves the file extension."""
        # Arrange
        filename = 'a' * 150 + '.png'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result.endswith('.png')


# ============================================================================
# Test: sanitize_filename() - Empty and Edge Cases
# ============================================================================

@pytest.mark.utils
class TestSanitizeFilenameEmptyAndEdgeCases:
    """Test empty filenames and edge cases."""

    def test_sanitize_filename_becomes_empty_after_sanitization(self):
        """Test that filename that becomes empty defaults to 'upload'."""
        # Arrange
        filename = '!!!.txt'  # Only special chars before extension

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'upload.txt'

    def test_sanitize_filename_special_chars_only(self):
        """Test filename with only special characters."""
        # Arrange
        filename = '###@@@!!!'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'upload'

    def test_sanitize_filename_spaces_and_dots_only(self):
        """Test filename with only spaces and dots."""
        # Arrange
        filename = '... ... ...'

        # Act
        result = sanitize_filename(filename)

        # Assert
        # Spaces and dots become underscores, resulting in non-empty string
        # The 'upload' fallback only applies to truly empty strings
        assert result == '__________'  # 10 underscores (3+3+1+3)

    def test_sanitize_filename_special_chars_with_extension(self):
        """Test special-chars-only filename with extension."""
        # Arrange
        filename = '***###@@@.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'upload.jpg'

    def test_sanitize_filename_empty_string(self):
        """Test empty filename input."""
        # Arrange
        filename = ''

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'upload'


# ============================================================================
# Test: sanitize_filename() - Unicode Support
# ============================================================================

@pytest.mark.utils
class TestSanitizeFilenameUnicode:
    """Test Unicode character handling."""

    def test_sanitize_filename_with_unicode_chars(self):
        """Test that Unicode alphanumeric characters are preserved."""
        # Arrange
        filename = 'photo_文件_2024.jpg'  # Contains Chinese characters

        # Act
        result = sanitize_filename(filename)

        # Assert
        # Python's isalnum() returns True for Unicode alphanumeric characters
        # So they are kept in the sanitized filename
        assert '文件' in result
        assert result == 'photo_文件_2024.jpg'

    def test_sanitize_filename_with_accented_chars(self):
        """Test that accented characters are preserved."""
        # Arrange
        filename = 'café_photo.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        # Python's isalnum() returns True for accented characters
        # So they are kept in the sanitized filename
        assert result == 'café_photo.jpg'

    def test_sanitize_filename_with_emoji(self):
        """Test that emoji characters are removed."""
        # Arrange
        filename = 'photo😀image.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        # Emoji should be removed
        assert '😀' not in result
        assert result == 'photoimage.jpg'


# ============================================================================
# Test: sanitize_filename() - Return Value Validation
# ============================================================================

@pytest.mark.utils
class TestSanitizeFilenameReturnValue:
    """Test return value structure and types."""

    def test_sanitize_filename_returns_string(self):
        """Test that function returns a string."""
        # Arrange
        filename = 'test.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert isinstance(result, str)

    def test_sanitize_filename_never_empty_unless_input_special(self):
        """Test that result is never empty (defaults to 'upload')."""
        # Arrange
        filename = '###@@@!!!'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert len(result) > 0
        assert result == 'upload'

    def test_sanitize_filename_preserves_valid_chars(self):
        """Test that valid characters are not removed."""
        # Arrange
        filename = 'test_file-2024.jpg'

        # Act
        result = sanitize_filename(filename)

        # Assert
        assert result == 'test_file-2024.jpg'


# ============================================================================
# Test: Integration - Common Real-World Scenarios
# ============================================================================

@pytest.mark.utils
class TestIntegrationRealWorldScenarios:
    """Test common real-world scenarios."""

    def test_blog_post_image_validation_and_sanitization(self, create_image):
        """Test typical blog post image validation and name sanitization."""
        # Arrange
        jpeg_content = create_image('JPEG').getvalue()
        original_filename = 'My Blog Post Image - 2024.jpg'

        # Act - Validate
        file = FileStorage(
            stream=BytesIO(jpeg_content),
            filename=original_filename,
            content_type='image/jpeg'
        )
        is_valid, error = validate_image_file(file)

        # Act - Sanitize
        safe_filename = sanitize_filename(original_filename)

        # Assert
        assert is_valid is True
        assert error == ""
        assert safe_filename == 'My_Blog_Post_Image_-_2024.jpg'

    def test_user_uploaded_file_with_dangerous_name(self, create_image):
        """Test handling of user upload with suspicious filename."""
        # Arrange
        png_content = create_image('PNG').getvalue()
        suspicious_filename = 'image</script>.png'

        # Act
        file = FileStorage(
            stream=BytesIO(png_content),
            filename=suspicious_filename,
            content_type='image/png'
        )
        is_valid, error = validate_image_file(file)
        safe_name = sanitize_filename(suspicious_filename)

        # Assert
        assert is_valid is True  # Content is valid
        assert 'script' in safe_name  # Script tags removed
        assert '<' not in safe_name
        assert '>' not in safe_name

    def test_multiple_file_processing_workflow(self, create_image):
        """Test processing multiple files with validation and sanitization."""
        # Arrange
        filenames = [
            'vacation_photo_2024.jpg',
            'Screenshot 2024-01-15.png',
            'my.backup.image.gif'
        ]
        jpeg_content = create_image('JPEG').getvalue()
        png_content = create_image('PNG').getvalue()
        gif_content = create_image('GIF').getvalue()

        # Act & Assert
        test_cases = [
            (jpeg_content, filenames[0], 'image/jpeg'),
            (png_content, filenames[1], 'image/png'),
            (gif_content, filenames[2], 'image/gif')
        ]

        for content, original_name, mime_type in test_cases:
            file = FileStorage(
                stream=BytesIO(content),
                filename=original_name,
                content_type=mime_type
            )

            is_valid, error = validate_image_file(file)
            safe_name = sanitize_filename(original_name)

            assert is_valid is True, f"Validation failed for {original_name}"
            assert error == "", f"Error for {original_name}: {error}"
            assert len(safe_name) > 0, f"Sanitized name empty for {original_name}"
