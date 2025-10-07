"""File upload validation utilities for security"""
import os
from io import BytesIO
from PIL import Image
from werkzeug.datastructures import FileStorage

# Allowed image file extensions
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

# Allowed MIME types for images
ALLOWED_IMAGE_MIMES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp'
}

# Maximum file size: 5MB (configurable, falls back to Flask's MAX_CONTENT_LENGTH)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB in bytes


def validate_image_file(file: FileStorage, max_size: int = MAX_IMAGE_SIZE) -> tuple[bool, str]:
    """
    Comprehensive image file validation with security checks.

    Args:
        file: The FileStorage object from Flask request
        max_size: Maximum allowed file size in bytes

    Returns:
        tuple: (is_valid: bool, error_message: str)

    Security checks:
        - File presence and non-empty content
        - File size limits
        - Extension whitelist
        - MIME type validation
        - Magic number verification (actual file type)
    """
    # Check if file is present
    if not file:
        return False, "No file provided"

    # Check if file has a filename
    if not file.filename or file.filename == '':
        return False, "No file selected"

    # Get file extension
    filename = file.filename.lower()
    if '.' not in filename:
        return False, "File has no extension"

    extension = filename.rsplit('.', 1)[1]

    # Validate extension against whitelist
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"File type .{extension} not allowed. Allowed types: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"

    # Check MIME type
    if file.content_type not in ALLOWED_IMAGE_MIMES:
        return False, f"Invalid file type. MIME type {file.content_type} not allowed"

    # Read file to check size and magic number
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    # Validate file size
    if file_size == 0:
        return False, "File is empty"

    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        return False, f"File too large ({actual_mb:.2f}MB). Maximum size: {max_mb:.0f}MB"

    # Validate magic number (actual file type) using Pillow
    # Read file content for validation
    file.seek(0)
    file_content = file.read()
    file.seek(0)  # Reset again for later use

    # Try to open as image and detect actual type
    try:
        img = Image.open(BytesIO(file_content))
        detected_type = img.format.lower() if img.format else None
        img.close()
    except Exception:
        return False, "File does not appear to be a valid image"

    if not detected_type:
        return False, "Could not determine image type"

    # Map detected type to expected extension
    # PIL returns: 'JPEG', 'PNG', 'GIF', 'WEBP', etc. (we lowercased it)
    valid_types = {
        'jpeg': ['jpg', 'jpeg'],
        'png': ['png'],
        'gif': ['gif'],
        'webp': ['webp']
    }

    # Check if detected type matches claimed extension
    extension_valid = False
    for img_type, valid_exts in valid_types.items():
        if detected_type == img_type and extension in valid_exts:
            extension_valid = True
            break

    if not extension_valid:
        return False, f"File extension .{extension} does not match actual file type ({detected_type})"

    # All validations passed
    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing special characters and ensuring safe names.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem storage
    """
    # Get extension
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
    else:
        name = filename
        ext = ''

    # Remove or replace unsafe characters
    # Keep only alphanumeric, dash, underscore
    safe_chars = []
    for char in name:
        if char.isalnum() or char in ('-', '_'):
            safe_chars.append(char)
        elif char in (' ', '.'):
            safe_chars.append('_')

    safe_name = ''.join(safe_chars)

    # Ensure filename is not empty after sanitization
    if not safe_name:
        safe_name = 'upload'

    # Limit filename length (reserve space for timestamp/uuid if needed)
    safe_name = safe_name[:100]

    # Reconstruct with extension
    if ext:
        return f"{safe_name}.{ext.lower()}"
    return safe_name
