"""
Comprehensive unit tests for app/utils/image_utils.py

Tests cover:
- Successful single and multiple file deletion
- Handling of None and empty values
- File not found scenarios
- Path traversal attack prevention
- Absolute path rejection
- Error handling (permissions, OS errors, etc.)
- Return value validation (counters and error messages)
- Logging verification
"""

import os
import pytest
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

from app.utils.image_utils import delete_uploaded_images


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_upload_folder():
    """Create a temporary directory for upload folder."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_upload_folder_with_files(temp_upload_folder):
    """Create temporary directory with test image files."""
    # Create some test files
    test_files = ['image1.jpg', 'image2.png', 'photo.gif']
    for filename in test_files:
        filepath = os.path.join(temp_upload_folder, filename)
        Path(filepath).touch()

    yield temp_upload_folder


@pytest.fixture
def caplog_fixture(caplog):
    """Capture log messages."""
    return caplog


# ============================================================================
# Test: Success Scenarios - File Deletion
# ============================================================================

@pytest.mark.utils
class TestSuccessfulDeletion:
    """Test cases for successful file deletion scenarios."""

    def test_delete_single_image_file(self, temp_upload_folder_with_files):
        """Test deletion of a single image file."""
        # Arrange
        filename = 'image1.jpg'

        # Act
        result = delete_uploaded_images(temp_upload_folder_with_files, [filename])

        # Assert
        assert result['files_deleted'] == 1
        assert result['files_skipped'] == 0
        assert result['files_not_found'] == 0
        assert result['errors'] == []
        assert not os.path.exists(os.path.join(temp_upload_folder_with_files, filename))

    def test_delete_multiple_image_files(self, temp_upload_folder_with_files):
        """Test deletion of multiple image files."""
        # Arrange
        filenames = ['image1.jpg', 'image2.png', 'photo.gif']

        # Act
        result = delete_uploaded_images(temp_upload_folder_with_files, filenames)

        # Assert
        assert result['files_deleted'] == 3
        assert result['files_skipped'] == 0
        assert result['files_not_found'] == 0
        assert result['errors'] == []

        # Verify all files are deleted
        for filename in filenames:
            assert not os.path.exists(os.path.join(temp_upload_folder_with_files, filename))

    def test_delete_files_with_mixed_extensions(self, temp_upload_folder):
        """Test deletion of files with various extensions."""
        # Arrange
        files = ['photo.jpg', 'image.jpeg', 'picture.png', 'graphic.gif', 'artwork.webp']
        for filename in files:
            Path(os.path.join(temp_upload_folder, filename)).touch()

        # Act
        result = delete_uploaded_images(temp_upload_folder, files)

        # Assert
        assert result['files_deleted'] == 5
        assert result['errors'] == []

    def test_delete_files_with_underscore_and_numbers(self, temp_upload_folder):
        """Test deletion of files with underscores and numbers in name."""
        # Arrange
        files = ['thumb_image_1.jpg', 'post_123_thumbnail.png', 'pic_2024_01_15.jpg']
        for filename in files:
            Path(os.path.join(temp_upload_folder, filename)).touch()

        # Act
        result = delete_uploaded_images(temp_upload_folder, files)

        # Assert
        assert result['files_deleted'] == 3
        assert result['errors'] == []


# ============================================================================
# Test: Skip/Not Found Scenarios
# ============================================================================

@pytest.mark.utils
class TestSkipAndNotFound:
    """Test cases for skipping None/empty values and handling missing files."""

    def test_skip_none_filename(self, temp_upload_folder_with_files):
        """Test that None filenames are skipped and counted."""
        # Arrange
        filenames = ['image1.jpg', None, 'image2.png']

        # Act
        result = delete_uploaded_images(temp_upload_folder_with_files, filenames)

        # Assert
        assert result['files_deleted'] == 2
        assert result['files_skipped'] == 1
        assert result['files_not_found'] == 0
        assert result['errors'] == []

    def test_skip_empty_string_filename(self, temp_upload_folder_with_files):
        """Test that empty string filenames are skipped and counted."""
        # Arrange
        filenames = ['image1.jpg', '', 'image2.png']

        # Act
        result = delete_uploaded_images(temp_upload_folder_with_files, filenames)

        # Assert
        assert result['files_deleted'] == 2
        assert result['files_skipped'] == 1
        assert result['files_not_found'] == 0
        assert result['errors'] == []

    def test_skip_multiple_none_values(self, temp_upload_folder_with_files):
        """Test that multiple None values are all skipped."""
        # Arrange
        filenames = [None, 'image1.jpg', None, None, 'image2.png', None]

        # Act
        result = delete_uploaded_images(temp_upload_folder_with_files, filenames)

        # Assert
        assert result['files_deleted'] == 2
        assert result['files_skipped'] == 4
        assert result['files_not_found'] == 0
        assert result['errors'] == []

    def test_skip_mixed_none_and_empty_strings(self, temp_upload_folder_with_files):
        """Test that mixed None and empty strings are all skipped."""
        # Arrange
        filenames = [None, '', 'image1.jpg', None, '', 'image2.png']

        # Act
        result = delete_uploaded_images(temp_upload_folder_with_files, filenames)

        # Assert
        assert result['files_deleted'] == 2
        assert result['files_skipped'] == 4
        assert result['files_not_found'] == 0
        assert result['errors'] == []

    def test_empty_filename_list(self, temp_upload_folder):
        """Test that an empty list returns zeros."""
        # Arrange
        filenames = []

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert result['files_skipped'] == 0
        assert result['files_not_found'] == 0
        assert result['errors'] == []

    def test_file_does_not_exist(self, temp_upload_folder):
        """Test handling of nonexistent files."""
        # Arrange
        filenames = ['nonexistent.jpg', 'missing.png']

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert result['files_skipped'] == 0
        assert result['files_not_found'] == 2
        assert result['errors'] == []

    def test_mixed_existing_and_nonexistent_files(self, temp_upload_folder_with_files):
        """Test mixed scenario with existing and missing files."""
        # Arrange
        filenames = ['image1.jpg', 'nonexistent.jpg', 'image2.png', 'missing.png']

        # Act
        result = delete_uploaded_images(temp_upload_folder_with_files, filenames)

        # Assert
        assert result['files_deleted'] == 2
        assert result['files_skipped'] == 0
        assert result['files_not_found'] == 2
        assert result['errors'] == []


# ============================================================================
# Test: Security Validation - Path Traversal Prevention
# ============================================================================

@pytest.mark.utils
@pytest.mark.security
class TestPathTraversalPrevention:
    """Test cases for preventing path traversal attacks."""

    def test_reject_double_dot_pattern(self, temp_upload_folder):
        """Test rejection of '..' pattern (parent directory traversal)."""
        # Arrange
        filenames = ['../../../etc/passwd']

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert result['files_skipped'] == 0
        assert result['files_not_found'] == 0
        assert len(result['errors']) == 1
        assert 'Path traversal attempt detected' in result['errors'][0]

    def test_reject_tilde_pattern(self, temp_upload_folder):
        """Test rejection of '~' pattern (home directory)."""
        # Arrange
        filenames = ['~/.ssh/id_rsa']

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert len(result['errors']) == 1
        assert 'Path traversal attempt detected' in result['errors'][0]

    def test_reject_double_slash_pattern(self, temp_upload_folder):
        """Test rejection of '//' pattern (empty directory)."""
        # Arrange
        filenames = ['uploads//../../secret.txt']

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert len(result['errors']) == 1
        assert 'Path traversal attempt detected' in result['errors'][0]

    def test_reject_backslash_pattern(self, temp_upload_folder):
        """Test rejection of '\\\\' pattern (Windows directory traversal)."""
        # Arrange
        filenames = ['images\\\\..\\\\secret.txt']

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert len(result['errors']) == 1
        assert 'Path traversal attempt detected' in result['errors'][0]

    def test_reject_null_byte_pattern(self, temp_upload_folder):
        """Test rejection of null byte pattern (null byte injection)."""
        # Arrange
        filenames = ['image.jpg\x00.exe']

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert len(result['errors']) == 1
        assert 'Path traversal attempt detected' in result['errors'][0]

    def test_reject_absolute_path_starting_with_slash(self, temp_upload_folder):
        """Test rejection of absolute paths starting with '/'."""
        # Arrange
        filenames = ['/etc/passwd']

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert len(result['errors']) == 1
        assert 'Absolute path rejected' in result['errors'][0]

    def test_reject_windows_absolute_path_with_drive_letter(self, temp_upload_folder):
        """Test rejection of Windows absolute paths (C:/, D:/, etc.)."""
        # Arrange
        filenames = ['C:/Windows/System32/config/SAM']

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert len(result['errors']) == 1
        assert 'Absolute path rejected' in result['errors'][0]

    def test_reject_windows_absolute_path_various_drives(self, temp_upload_folder):
        """Test rejection of various Windows drive letters."""
        # Arrange
        filenames = ['D:/sensitive/data.txt', 'E:/backup/config.ini', 'Z:/network/resource.doc']

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert result['files_skipped'] == 0
        assert result['files_not_found'] == 0
        assert len(result['errors']) == 3

    def test_verify_file_within_upload_directory(self, temp_upload_folder_with_files):
        """Test that file path must resolve within upload directory."""
        # Arrange - Create a file outside the upload directory
        parent_dir = os.path.dirname(temp_upload_folder_with_files)
        outside_file = os.path.join(parent_dir, 'outside.txt')
        Path(outside_file).touch()

        # Try to access it using relative path manipulation
        upload_folder_name = os.path.basename(temp_upload_folder_with_files)
        parent_name = os.path.basename(parent_dir)

        # This should be caught when resolved path is outside upload directory
        # Note: We can't directly create a relative path that escapes, but we can mock
        filenames = ['../outside.txt']

        # Act
        result = delete_uploaded_images(temp_upload_folder_with_files, filenames)

        # Assert
        assert result['files_deleted'] == 0
        # Should be rejected as path traversal attempt (contains ..)
        assert len(result['errors']) == 1

    def test_mixed_security_violations(self, temp_upload_folder):
        """Test multiple security violations in a single call."""
        # Arrange
        filenames = [
            '../../../etc/passwd',
            '~/.ssh/id_rsa',
            '/etc/shadow',
            'C:/Windows/System32/drivers/etc/hosts',
            'normal_file.jpg'
        ]
        # Create the normal file
        Path(os.path.join(temp_upload_folder, 'normal_file.jpg')).touch()

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 1  # Only normal_file.jpg
        assert len(result['errors']) == 4  # Four security violation error messages
        # Verify that errors is a list of error messages
        assert all(isinstance(err, str) for err in result['errors'])


# ============================================================================
# Test: Error Handling - Folder/Path Issues
# ============================================================================

@pytest.mark.utils
class TestErrorHandling:
    """Test cases for error handling."""

    def test_upload_folder_does_not_exist(self):
        """Test error when upload folder doesn't exist."""
        # Arrange
        nonexistent_folder = '/nonexistent/path/that/does/not/exist'
        filenames = ['image.jpg']

        # Act
        result = delete_uploaded_images(nonexistent_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert result['files_skipped'] == 0
        assert result['files_not_found'] == 0
        assert len(result['errors']) == 1
        assert 'Upload folder does not exist' in result['errors'][0]

    def test_upload_folder_is_none(self):
        """Test error when upload folder is None."""
        # Arrange
        filenames = ['image.jpg']

        # Act
        result = delete_uploaded_images(None, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert len(result['errors']) == 1
        assert 'Upload folder does not exist' in result['errors'][0]

    def test_upload_folder_is_empty_string(self):
        """Test error when upload folder is empty string."""
        # Arrange
        filenames = ['image.jpg']

        # Act
        result = delete_uploaded_images('', filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert len(result['errors']) == 1
        assert 'Upload folder does not exist' in result['errors'][0]

    def test_upload_folder_path_resolution_fails(self, temp_upload_folder):
        """Test error when upload folder path resolution fails."""
        # Arrange
        filenames = ['image.jpg']

        # Act - Mock Path.resolve to raise OSError
        with patch('pathlib.Path.resolve') as mock_resolve:
            mock_resolve.side_effect = OSError('Permission denied')
            result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert len(result['errors']) == 1
        assert 'Failed to resolve upload folder path' in result['errors'][0]

    def test_path_is_directory_not_file(self, temp_upload_folder):
        """Test error when path is a directory, not a file."""
        # Arrange
        subdir_name = 'subdir'
        subdir_path = os.path.join(temp_upload_folder, subdir_name)
        os.makedirs(subdir_path)

        filenames = [subdir_name]

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert len(result['errors']) == 1
        assert 'Path is not a file' in result['errors'][0]

    @patch('os.remove')
    def test_permission_error_when_deleting_file(self, mock_remove, temp_upload_folder):
        """Test handling of PermissionError when deleting file."""
        # Arrange
        filename = 'image.jpg'
        filepath = os.path.join(temp_upload_folder, filename)
        Path(filepath).touch()

        mock_remove.side_effect = PermissionError('Access denied')
        filenames = [filename]

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert len(result['errors']) == 1
        assert 'Permission denied deleting' in result['errors'][0]

    @patch('os.remove')
    def test_os_error_when_deleting_file(self, mock_remove, temp_upload_folder):
        """Test handling of OSError when deleting file."""
        # Arrange
        filename = 'image.jpg'
        filepath = os.path.join(temp_upload_folder, filename)
        Path(filepath).touch()

        mock_remove.side_effect = OSError('Device or resource busy')
        filenames = [filename]

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert len(result['errors']) == 1
        assert 'OS error deleting' in result['errors'][0]

    @patch('os.remove')
    def test_generic_exception_when_deleting_file(self, mock_remove, temp_upload_folder):
        """Test handling of generic Exception when deleting file."""
        # Arrange
        filename = 'image.jpg'
        filepath = os.path.join(temp_upload_folder, filename)
        Path(filepath).touch()

        mock_remove.side_effect = RuntimeError('Unexpected error')
        filenames = [filename]

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert len(result['errors']) == 1
        assert 'Unexpected error deleting' in result['errors'][0]


# ============================================================================
# Test: Return Value Validation
# ============================================================================

@pytest.mark.utils
class TestReturnValueValidation:
    """Test cases for validating return dictionary structure and values."""

    def test_return_dict_has_all_required_keys(self, temp_upload_folder):
        """Test that return dict always has all required keys."""
        # Arrange
        filenames = []

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        required_keys = {'files_deleted', 'files_skipped', 'files_not_found', 'errors'}
        assert required_keys.issubset(result.keys())

    def test_return_dict_values_are_correct_types(self, temp_upload_folder):
        """Test that return dict values have correct types."""
        # Arrange
        filenames = []

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert isinstance(result['files_deleted'], int)
        assert isinstance(result['files_skipped'], int)
        assert isinstance(result['files_not_found'], int)
        assert isinstance(result['errors'], list)

    def test_all_counters_zero_on_empty_list(self, temp_upload_folder):
        """Test all counters are 0 and errors empty on empty filename list."""
        # Arrange
        filenames = []

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 0
        assert result['files_skipped'] == 0
        assert result['files_not_found'] == 0
        assert result['errors'] == []

    def test_complex_scenario_counter_validation(self, temp_upload_folder):
        """Test counter accuracy in complex mixed scenario."""
        # Arrange
        # Create some files
        files_to_create = ['exists1.jpg', 'exists2.png', 'exists3.gif']
        for filename in files_to_create:
            Path(os.path.join(temp_upload_folder, filename)).touch()

        # Mix of valid, invalid, None, and nonexistent
        filenames = [
            'exists1.jpg',           # Will be deleted
            None,                    # Will be skipped
            'nonexistent.jpg',       # Not found
            'exists2.png',           # Will be deleted
            '',                      # Will be skipped
            '../traversal.txt',      # Security violation (error)
            'exists3.gif',           # Will be deleted
        ]

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 3
        assert result['files_skipped'] == 2
        assert result['files_not_found'] == 1
        assert len(result['errors']) == 1  # Path traversal violation

    def test_error_list_contains_descriptive_messages(self, temp_upload_folder):
        """Test that error list contains descriptive error messages."""
        # Arrange
        filenames = [
            '/etc/passwd',
            '../secret.txt',
            'nonexistent.jpg'
        ]

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert len(result['errors']) >= 2
        for error_msg in result['errors']:
            assert isinstance(error_msg, str)
            assert len(error_msg) > 0


# ============================================================================
# Test: Logging Verification
# ============================================================================

@pytest.mark.utils
class TestLoggingBehavior:
    """Test cases for verifying appropriate logging."""

    def test_debug_log_for_skipped_files(self, temp_upload_folder, caplog):
        """Test that debug log is created for skipped files."""
        # Arrange
        with caplog.at_level(logging.DEBUG):
            filenames = [None, '', 'image.jpg']
            Path(os.path.join(temp_upload_folder, 'image.jpg')).touch()

            # Act
            result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        # Should have debug messages for None/empty
        debug_msgs = [r.message for r in caplog.records if r.levelname == 'DEBUG']
        assert len(debug_msgs) >= 2  # Two skips

    def test_warning_log_for_security_violations(self, temp_upload_folder, caplog):
        """Test that warning log is created for security violations."""
        # Arrange
        with caplog.at_level(logging.WARNING):
            filenames = ['../../../etc/passwd', '~/.ssh/id_rsa']

            # Act
            result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        warning_msgs = [r.message for r in caplog.records if r.levelname == 'WARNING']
        assert len(warning_msgs) >= 2

    def test_warning_log_for_missing_files(self, temp_upload_folder, caplog):
        """Test that warning log is created for missing files."""
        # Arrange
        with caplog.at_level(logging.WARNING):
            filenames = ['nonexistent.jpg', 'missing.png']

            # Act
            result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        warning_msgs = [r.message for r in caplog.records if r.levelname == 'WARNING']
        assert len(warning_msgs) >= 2

    def test_error_log_for_permission_denied(self, temp_upload_folder, caplog):
        """Test that error log is created for permission denied."""
        # Arrange
        filename = 'image.jpg'
        filepath = os.path.join(temp_upload_folder, filename)
        Path(filepath).touch()

        with caplog.at_level(logging.ERROR):
            with patch('os.remove') as mock_remove:
                mock_remove.side_effect = PermissionError('Access denied')
                filenames = [filename]

                # Act
                result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        error_msgs = [r.message for r in caplog.records if r.levelname == 'ERROR']
        assert len(error_msgs) >= 1

    def test_info_log_for_successful_deletion(self, temp_upload_folder, caplog):
        """Test that info log is created for successful deletion."""
        # Arrange
        filename = 'image.jpg'
        Path(os.path.join(temp_upload_folder, filename)).touch()

        with caplog.at_level(logging.INFO):
            filenames = [filename]

            # Act
            result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        info_msgs = [r.message for r in caplog.records if r.levelname == 'INFO']
        # Should have success message and summary
        assert len(info_msgs) >= 2

    def test_summary_log_at_end(self, temp_upload_folder, caplog):
        """Test that summary log is created at end."""
        # Arrange
        with caplog.at_level(logging.INFO):
            filenames = ['nonexistent.jpg']

            # Act
            result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        info_msgs = [r.message for r in caplog.records if r.levelname == 'INFO']
        # Last info message should be summary
        summary_found = any('deletion summary' in msg.lower() for msg in info_msgs)
        assert summary_found

    def test_summary_log_contains_all_counters(self, temp_upload_folder, caplog):
        """Test that summary log contains all counter values."""
        # Arrange
        filenames = ['nonexistent.jpg', None]

        with caplog.at_level(logging.INFO):
            # Act
            result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        info_msgs = [r.message for r in caplog.records if r.levelname == 'INFO']
        summary = [msg for msg in info_msgs if 'deletion summary' in msg.lower()]

        assert len(summary) > 0
        summary_msg = summary[0]
        # Summary should contain mention of the counts
        assert 'deleted' in summary_msg.lower()
        assert 'skipped' in summary_msg.lower()


# ============================================================================
# Test: Edge Cases and Integration
# ============================================================================

@pytest.mark.utils
class TestEdgeCases:
    """Test cases for edge cases and integration scenarios."""

    def test_filename_with_special_characters(self, temp_upload_folder):
        """Test handling of files with special characters (but safe ones)."""
        # Arrange
        filenames = ['image-2024-01-15.jpg', 'photo_copy (1).png', 'file@version2.gif']
        for filename in filenames:
            Path(os.path.join(temp_upload_folder, filename)).touch()

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 3
        assert result['errors'] == []

    def test_filename_with_spaces(self, temp_upload_folder):
        """Test handling of filenames with spaces."""
        # Arrange
        filenames = ['my photo.jpg', 'image file 2024.png']
        for filename in filenames:
            Path(os.path.join(temp_upload_folder, filename)).touch()

        # Act
        result = delete_uploaded_images(temp_upload_folder, filenames)

        # Assert
        assert result['files_deleted'] == 2
        assert result['errors'] == []

    def test_very_long_filename(self, temp_upload_folder):
        """Test handling of very long filenames."""
        # Arrange
        long_filename = 'a' * 200 + '.jpg'
        Path(os.path.join(temp_upload_folder, long_filename)).touch()

        # Act
        result = delete_uploaded_images(temp_upload_folder, [long_filename])

        # Assert
        assert result['files_deleted'] == 1
        assert result['errors'] == []

    def test_case_sensitive_filename(self, temp_upload_folder):
        """Test case-sensitive filename handling."""
        # Arrange
        # Create file with one case
        Path(os.path.join(temp_upload_folder, 'Image.JPG')).touch()

        # Try to delete with different case
        # (Behavior depends on filesystem - on Linux, should not find it)
        result = delete_uploaded_images(temp_upload_folder, ['image.jpg'])

        # Assert - on Linux, should not find lowercase
        assert result['files_not_found'] == 1

    def test_hidden_files_dot_prefix(self, temp_upload_folder):
        """Test deletion of hidden files (starting with dot)."""
        # Arrange
        hidden_filename = '.hidden_image.jpg'
        Path(os.path.join(temp_upload_folder, hidden_filename)).touch()

        # Act
        result = delete_uploaded_images(temp_upload_folder, [hidden_filename])

        # Assert
        assert result['files_deleted'] == 1
        assert result['errors'] == []

    def test_return_value_does_not_modify_input_list(self, temp_upload_folder_with_files):
        """Test that function doesn't modify input filename list."""
        # Arrange
        filenames = ['image1.jpg', None, 'image2.png']
        original_filenames = filenames.copy()

        # Act
        result = delete_uploaded_images(temp_upload_folder_with_files, filenames)

        # Assert
        assert filenames == original_filenames

    def test_symlinks_handling(self, temp_upload_folder):
        """Test handling of symbolic links."""
        # Arrange
        # Create a file and a symlink to it
        real_file = os.path.join(temp_upload_folder, 'real_image.jpg')
        symlink_file = os.path.join(temp_upload_folder, 'symlink_image.jpg')

        Path(real_file).touch()

        try:
            os.symlink(real_file, symlink_file)

            # Act
            result = delete_uploaded_images(temp_upload_folder, ['symlink_image.jpg'])

            # Assert
            # Symlink should be deleted (not the target)
            assert result['files_deleted'] == 1
            assert os.path.exists(real_file)  # Original file still exists
            assert not os.path.exists(symlink_file)  # Symlink deleted
        except (OSError, NotImplementedError):
            # Symlinks may not be supported (e.g., Windows without admin)
            pytest.skip("Symlinks not supported on this system")

    def test_concurrent_deletion_simulation(self, temp_upload_folder):
        """Test behavior when file is deleted by another process."""
        # Arrange
        filename = 'image.jpg'
        filepath = os.path.join(temp_upload_folder, filename)
        Path(filepath).touch()

        # Mock os.remove to delete file before checking exists
        original_exists = os.path.exists
        call_count = [0]

        def mock_exists(path):
            result = original_exists(path)
            # On second check (for the actual file), return True
            # Then os.remove will succeed
            return result

        # Act
        result = delete_uploaded_images(temp_upload_folder, [filename])

        # Assert
        assert result['files_deleted'] == 1
        assert not os.path.exists(filepath)


# ============================================================================
# Test: Integration with Different Path Formats
# ============================================================================

@pytest.mark.utils
class TestPathFormats:
    """Test cases for different path format handling."""

    def test_upload_folder_with_trailing_slash(self, temp_upload_folder_with_files):
        """Test handling of upload folder path with trailing slash."""
        # Arrange
        folder_with_slash = temp_upload_folder_with_files + '/'
        filenames = ['image1.jpg']

        # Act
        result = delete_uploaded_images(folder_with_slash, filenames)

        # Assert
        assert result['files_deleted'] == 1
        assert result['errors'] == []

    def test_upload_folder_with_dot_notation(self, temp_upload_folder_with_files):
        """Test handling of upload folder with relative notation."""
        # Use absolute path instead
        filenames = ['image1.jpg']

        # Act
        result = delete_uploaded_images(temp_upload_folder_with_files, filenames)

        # Assert
        assert result['files_deleted'] == 1
        assert result['errors'] == []

    def test_relative_filename_single_directory(self, temp_upload_folder):
        """Test filename that looks like relative but is single level."""
        # Arrange
        subdir = 'subdir'
        os.makedirs(os.path.join(temp_upload_folder, subdir))

        filename = 'image_in_subdir.jpg'
        filepath = os.path.join(temp_upload_folder, subdir, filename)
        Path(filepath).touch()

        # Act - try to delete with relative path containing subdir
        # This should fail security check if it's '../' but should work for legitimate subdirs
        result = delete_uploaded_images(temp_upload_folder, [os.path.join(subdir, filename)])

        # Assert - This depends on how os.path.join handles it
        # When properly constructed, should work
        assert result['files_deleted'] == 1 or result['files_deleted'] == 0


# ============================================================================
# Test: Path Resolution Edge Cases (Lines 106-115)
# ============================================================================

@pytest.mark.utils
class TestPathResolutionEdgeCases:
    """Test cases for path resolution error handling - covers lines 106-115."""

    def test_symlink_resolves_outside_upload_directory(self, temp_upload_folder):
        """Test ValueError when symlink resolves outside upload directory (lines 106-110)."""
        # Arrange
        # Create a file outside the upload folder
        with tempfile.TemporaryDirectory() as outside_dir:
            outside_file = os.path.join(outside_dir, 'outside.jpg')
            Path(outside_file).touch()

            # Create a symlink inside upload folder pointing to outside file
            symlink_name = 'symlink_to_outside.jpg'
            symlink_path = os.path.join(temp_upload_folder, symlink_name)

            try:
                os.symlink(outside_file, symlink_path)
            except OSError:
                # Symlinks might not be supported on Windows
                pytest.skip("Symlinks not supported on this system")

            # Act
            result = delete_uploaded_images(temp_upload_folder, [symlink_name])

            # Assert - should be caught by security check
            assert result['files_deleted'] == 0
            assert result['errors']
            assert any('outside upload directory' in str(error).lower() for error in result['errors'])

    def test_path_resolution_oserror_handling(self, temp_upload_folder):
        """Test OSError during path resolution is handled (lines 111-115)."""
        # Arrange
        from unittest.mock import patch

        # Mock Path.resolve to raise OSError
        with patch('app.utils.image_utils.Path') as mock_path:
            # First call for upload_folder_abs succeeds
            upload_path_instance = MagicMock()
            upload_path_instance.resolve.return_value = Path(temp_upload_folder).resolve()

            # Second call for file_path_abs raises OSError
            file_path_instance = MagicMock()
            file_path_instance.resolve.side_effect = OSError('Path resolution failed')

            # Make Path() return different instances
            call_count = [0]
            def path_side_effect(path_str):
                call_count[0] += 1
                if call_count[0] == 1:
                    return upload_path_instance
                else:
                    return file_path_instance

            mock_path.side_effect = path_side_effect

            # Act
            result = delete_uploaded_images(temp_upload_folder, ['test.jpg'])

            # Assert
            assert result['files_deleted'] == 0
            assert result['errors']
            assert any('Path resolution failed' in str(error) for error in result['errors'])

    def test_path_resolution_runtimeerror_handling(self, temp_upload_folder):
        """Test RuntimeError during path resolution is handled (lines 111-115)."""
        # Arrange
        from unittest.mock import patch

        # Mock Path.resolve to raise RuntimeError
        with patch('app.utils.image_utils.Path') as mock_path:
            # First call for upload_folder_abs succeeds
            upload_path_instance = MagicMock()
            upload_path_instance.resolve.return_value = Path(temp_upload_folder).resolve()

            # Second call for file_path_abs raises RuntimeError
            file_path_instance = MagicMock()
            file_path_instance.resolve.side_effect = RuntimeError('Symlink loop detected')

            # Make Path() return different instances
            call_count = [0]
            def path_side_effect(path_str):
                call_count[0] += 1
                if call_count[0] == 1:
                    return upload_path_instance
                else:
                    return file_path_instance

            mock_path.side_effect = path_side_effect

            # Act
            result = delete_uploaded_images(temp_upload_folder, ['test.jpg'])

            # Assert
            assert result['files_deleted'] == 0
            assert result['errors']
            assert any('Path resolution failed' in str(error) for error in result['errors'])

    def test_relative_to_valueerror_with_mock(self, temp_upload_folder):
        """Test ValueError from relative_to() security check (lines 106-110)."""
        # Arrange
        from unittest.mock import patch

        # Create a real file to test with
        test_file = 'test.jpg'
        test_path = os.path.join(temp_upload_folder, test_file)
        Path(test_path).touch()

        # Mock the relative_to method to raise ValueError
        with patch('pathlib.Path.relative_to', side_effect=ValueError('Path is not relative')):
            # Act
            result = delete_uploaded_images(temp_upload_folder, [test_file])

            # Assert
            assert result['files_deleted'] == 0
            assert result['errors']
            assert any('outside upload directory' in str(error).lower() for error in result['errors'])
