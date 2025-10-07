import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def delete_uploaded_images(upload_folder: str, image_filenames: List[Optional[str]]) -> Dict[str, any]:
    """
    Safely delete uploaded image files with comprehensive error handling and security validation.

    This utility function handles deletion of image files from the uploads directory,
    with robust error handling, path traversal protection, and logging for audit trails.
    It gracefully handles None/empty filenames, missing files, and permission errors.

    Args:
        upload_folder (str): Path to the upload directory (e.g., 'uploads/blog-posts')
        image_filenames (List[Optional[str]]): List of image filenames to delete.
                                               None values are safely ignored.

    Returns:
        Dict[str, any]: Result dictionary containing:
            - 'files_deleted' (int): Count of successfully deleted files
            - 'files_skipped' (int): Count of files that were None or empty
            - 'files_not_found' (int): Count of files that didn't exist
            - 'errors' (List[str]): List of error messages for failed deletions

    Example:
        >>> result = delete_uploaded_images(
        ...     '/uploads/blog-posts',
        ...     ['image.jpg', 'thumb_image.jpg', None]
        ... )
        >>> print(result)
        {'files_deleted': 2, 'files_skipped': 1, 'files_not_found': 0, 'errors': []}

    Security:
        - Validates filenames are not None/empty before processing
        - Prevents path traversal attacks by validating resolved paths
        - Uses os.path.join() for safe path construction
        - Ensures files are within the specified upload directory
        - Logs all deletion attempts for audit trail
        - Catches and logs permission errors without raising exceptions

    Notes:
        - Does not raise exceptions - all errors are logged and returned
        - Missing files are logged as warnings but not counted as errors
        - Designed to be called after database deletion for cleanup safety
    """
    result = {
        'files_deleted': 0,
        'files_skipped': 0,
        'files_not_found': 0,
        'errors': []
    }

    # Validate upload_folder exists
    if not upload_folder or not os.path.exists(upload_folder):
        error_msg = f"Upload folder does not exist: {upload_folder}"
        logger.error(error_msg)
        result['errors'].append(error_msg)
        return result

    # Resolve upload folder to absolute path for security checks
    try:
        upload_folder_abs = Path(upload_folder).resolve()
    except (OSError, RuntimeError) as e:
        error_msg = f"Failed to resolve upload folder path: {str(e)}"
        logger.error(error_msg)
        result['errors'].append(error_msg)
        return result

    # Process each filename
    for filename in image_filenames:
        # Skip None or empty filenames
        if not filename:
            result['files_skipped'] += 1
            logger.debug(f"Skipped None/empty filename in deletion request")
            continue

        # Security: Check for path traversal patterns
        dangerous_patterns = ['..', '~', '//', '\\\\', '\x00']
        if any(pattern in filename for pattern in dangerous_patterns):
            error_msg = f"Path traversal attempt detected in filename: {filename}"
            logger.warning(error_msg)
            result['errors'].append(error_msg)
            continue

        # Security: Reject absolute paths in filenames
        if filename.startswith('/') or (len(filename) > 1 and filename[1] == ':'):
            error_msg = f"Absolute path rejected in filename: {filename}"
            logger.warning(error_msg)
            result['errors'].append(error_msg)
            continue

        # Construct full file path
        file_path = os.path.join(upload_folder, filename)

        # Security: Resolve path and verify it's within upload directory
        try:
            file_path_abs = Path(file_path).resolve(strict=False)

            # Verify resolved path is within upload directory
            try:
                file_path_abs.relative_to(upload_folder_abs)
            except ValueError:
                error_msg = f"Security: File path outside upload directory: {filename}"
                logger.warning(error_msg)
                result['errors'].append(error_msg)
                continue
        except (OSError, RuntimeError) as e:
            error_msg = f"Path resolution failed for {filename}: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            continue

        # Check if file exists
        if not os.path.exists(file_path):
            result['files_not_found'] += 1
            logger.warning(f"Image file not found (already deleted or never existed): {filename}")
            continue

        # Verify it's actually a file (not a directory)
        if not os.path.isfile(file_path):
            error_msg = f"Path is not a file: {filename}"
            logger.warning(error_msg)
            result['errors'].append(error_msg)
            continue

        # Attempt to delete the file
        try:
            os.remove(file_path)
            result['files_deleted'] += 1
            logger.info(f"Successfully deleted image file: {filename}")
        except PermissionError as e:
            error_msg = f"Permission denied deleting {filename}: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        except OSError as e:
            error_msg = f"OS error deleting {filename}: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error deleting {filename}: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)

    # Log summary
    logger.info(
        f"Image deletion summary: {result['files_deleted']} deleted, "
        f"{result['files_skipped']} skipped, {result['files_not_found']} not found, "
        f"{len(result['errors'])} errors"
    )

    return result
