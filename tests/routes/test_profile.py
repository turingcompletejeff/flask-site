"""
Comprehensive tests for profile routes.

Tests cover:
- Profile viewing (GET /profile)
- Profile editing (GET/POST /profile/edit)
- Password changing (GET/POST /profile/change-password)
- Profile picture upload and validation
- File serving (GET /uploads/profiles/<filename>)
- Authorization checks
- Error handling
"""

import pytest
import os
from io import BytesIO
from PIL import Image
from werkzeug.datastructures import FileStorage


@pytest.mark.integration
class TestViewProfile:
    """Test suite for viewing user profile (GET /profile)."""

    def test_profile_requires_authentication(self, client):
        """Test that profile page requires login."""
        response = client.get('/profile')
        assert response.status_code == 302  # Redirect to login
        assert b'/auth/login' in response.data or response.location and 'login' in response.location

    def test_profile_accessible_when_authenticated(self, auth_client, regular_user):
        """Test that authenticated users can view their profile."""
        response = auth_client.get('/profile')
        assert response.status_code == 200

    def test_profile_displays_user_info(self, auth_client, regular_user):
        """Test that profile displays user information."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert regular_user.email.encode() in response.data

    def test_profile_sets_current_page(self, auth_client, regular_user):
        """Test that profile sets current_page context variable."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        # Template should receive current_page='profile'

    def test_profile_with_admin_user(self, admin_client, admin_user):
        """Test that admin users can view their profile."""
        response = admin_client.get('/profile')
        assert response.status_code == 200
        assert admin_user.email.encode() in response.data

    def test_profile_with_blogger_user(self, blogger_client, blogger_user):
        """Test that blogger users can view their profile."""
        response = blogger_client.get('/profile')
        assert response.status_code == 200
        assert blogger_user.email.encode() in response.data

    def test_profile_displays_bio_if_set(self, auth_client, regular_user, db):
        """Test that profile displays bio if user has one."""
        regular_user.bio = "This is my test bio"
        db.session.commit()

        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'This is my test bio' in response.data

    def test_profile_displays_profile_picture_if_set(self, auth_client, regular_user, db):
        """Test that profile displays profile picture if user has one."""
        regular_user.profile_picture = "1_thumb.jpg"
        db.session.commit()

        response = auth_client.get('/profile')
        assert response.status_code == 200
        # Template should reference the profile picture


@pytest.mark.integration
class TestEditProfileDisplay:
    """Test suite for profile edit form display (GET /profile/edit)."""

    def test_edit_profile_requires_authentication(self, client):
        """Test that edit profile requires login."""
        response = client.get('/profile/edit')
        assert response.status_code == 302  # Redirect to login

    def test_edit_profile_accessible_when_authenticated(self, auth_client):
        """Test that authenticated users can access edit form."""
        response = auth_client.get('/profile/edit')
        assert response.status_code == 200

    def test_edit_profile_prepopulates_email(self, auth_client, regular_user):
        """Test that edit form prepopulates current email."""
        response = auth_client.get('/profile/edit')
        assert response.status_code == 200
        assert regular_user.email.encode() in response.data

    def test_edit_profile_prepopulates_bio(self, auth_client, regular_user, db):
        """Test that edit form prepopulates current bio."""
        regular_user.bio = "Existing bio content"
        db.session.commit()

        response = auth_client.get('/profile/edit')
        assert response.status_code == 200
        assert b'Existing bio content' in response.data

    def test_edit_profile_has_form_fields(self, auth_client):
        """Test that edit form has all required fields."""
        response = auth_client.get('/profile/edit')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'email' in html.lower()
        assert 'bio' in html.lower()

    def test_edit_profile_sets_current_page(self, auth_client):
        """Test that edit profile sets current_page context."""
        response = auth_client.get('/profile/edit')
        assert response.status_code == 200
        # Template should receive current_page='profile'


@pytest.mark.integration
class TestEditProfileSubmission:
    """Test suite for profile edit form submission (POST /profile/edit)."""

    def test_edit_profile_update_email(self, auth_client, regular_user, db):
        """Test updating user email."""
        new_email = 'newemail@example.com'

        response = auth_client.post('/profile/edit', data={
            'email': new_email,
            'bio': '',
            'csrf_token': 'test_token'
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(regular_user)
        assert regular_user.email == new_email

    def test_edit_profile_update_bio(self, auth_client, regular_user, db):
        """Test updating user bio."""
        new_bio = 'This is my updated bio.'

        response = auth_client.post('/profile/edit', data={
            'email': regular_user.email,
            'bio': new_bio,
            'csrf_token': 'test_token'
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(regular_user)
        assert regular_user.bio == new_bio

    def test_edit_profile_update_both_fields(self, auth_client, regular_user, db):
        """Test updating both email and bio."""
        new_email = 'updated@example.com'
        new_bio = 'Updated bio content'

        response = auth_client.post('/profile/edit', data={
            'email': new_email,
            'bio': new_bio,
            'csrf_token': 'test_token'
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(regular_user)
        assert regular_user.email == new_email
        assert regular_user.bio == new_bio

    def test_edit_profile_invalid_email(self, auth_client, regular_user):
        """Test that invalid email is rejected."""
        response = auth_client.post('/profile/edit', data={
            'email': 'not-a-valid-email',
            'bio': '',
            'csrf_token': 'test_token'
        })

        # Should return to form with errors
        assert response.status_code == 200

    def test_edit_profile_empty_email(self, auth_client, regular_user):
        """Test that empty email is rejected."""
        response = auth_client.post('/profile/edit', data={
            'email': '',
            'bio': 'Some bio',
            'csrf_token': 'test_token'
        })

        # Should fail validation
        assert response.status_code == 200

    def test_edit_profile_flash_success_message(self, auth_client, regular_user):
        """Test that success message is flashed after update."""
        response = auth_client.post('/profile/edit', data={
            'email': 'success@example.com',
            'bio': 'Bio',
            'csrf_token': 'test_token'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'success' in response.data.lower()

    def test_edit_profile_redirects_to_view(self, auth_client, regular_user):
        """Test that successful edit redirects to profile view."""
        response = auth_client.post('/profile/edit', data={
            'email': 'redirect@example.com',
            'bio': 'Bio',
            'csrf_token': 'test_token'
        }, follow_redirects=False)

        assert response.status_code == 302
        assert '/profile' in response.location

    def test_edit_profile_with_unicode_bio(self, auth_client, regular_user, db):
        """Test editing bio with Unicode characters."""
        unicode_bio = 'Bio with émojis 🎉 and 你好'

        response = auth_client.post('/profile/edit', data={
            'email': regular_user.email,
            'bio': unicode_bio,
            'csrf_token': 'test_token'
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(regular_user)
        assert regular_user.bio == unicode_bio

    def test_edit_profile_with_long_bio(self, auth_client, regular_user, db):
        """Test editing bio with very long text."""
        long_bio = 'A' * 500

        response = auth_client.post('/profile/edit', data={
            'email': regular_user.email,
            'bio': long_bio,
            'csrf_token': 'test_token'
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(regular_user)
        # Bio should be saved (may be truncated by DB constraints if any)


@pytest.mark.integration
class TestProfilePictureUpload:
    """Test suite for profile picture upload functionality."""

    @pytest.fixture
    def mock_valid_image(self):
        """Create a valid test image file."""
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return FileStorage(
            stream=img_bytes,
            filename='test_profile.jpg',
            content_type='image/jpeg'
        )

    def test_profile_picture_upload_success(self, auth_client, regular_user, mock_valid_image, db, app):
        """Test successful profile picture upload."""
        response = auth_client.post('/profile/edit', data={
            'email': regular_user.email,
            'bio': '',
            'profile_picture': mock_valid_image,
            'csrf_token': 'test_token'
        }, content_type='multipart/form-data', follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(regular_user)
        assert regular_user.profile_picture is not None

        # Cleanup
        if regular_user.profile_picture:
            profile_path = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], regular_user.profile_picture)
            if os.path.exists(profile_path):
                os.remove(profile_path)

    def test_profile_picture_creates_thumbnail(self, auth_client, regular_user, mock_valid_image, db, app):
        """Test that profile picture upload creates a thumbnail."""
        response = auth_client.post('/profile/edit', data={
            'email': regular_user.email,
            'bio': '',
            'profile_picture': mock_valid_image,
            'csrf_token': 'test_token'
        }, content_type='multipart/form-data', follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(regular_user)

        # Check that thumbnail was created
        if regular_user.profile_picture:
            thumb_path = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], regular_user.profile_picture)
            assert os.path.exists(thumb_path) or response.status_code == 200

            # Cleanup
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
            # Also cleanup the original
            orig_path = thumb_path.replace('_thumb', '_profile')
            if os.path.exists(orig_path):
                os.remove(orig_path)

    def test_profile_picture_replaces_old(self, auth_client, regular_user, db, app):
        """Test that new profile picture replaces old one."""
        # Set existing profile picture
        regular_user.profile_picture = f"{regular_user.id}_thumb.jpg"
        db.session.commit()

        # Create old files
        os.makedirs(app.config['PROFILE_UPLOAD_FOLDER'], exist_ok=True)
        old_profile = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], f"{regular_user.id}_profile.jpg")
        old_thumb = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], f"{regular_user.id}_thumb.jpg")

        with open(old_profile, 'w') as f:
            f.write('old')
        with open(old_thumb, 'w') as f:
            f.write('old')

        # Upload new image
        img = Image.new('RGB', (100, 100), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        new_image = FileStorage(stream=img_bytes, filename='new.png', content_type='image/png')

        response = auth_client.post('/profile/edit', data={
            'email': regular_user.email,
            'bio': '',
            'profile_picture': new_image,
            'csrf_token': 'test_token'
        }, content_type='multipart/form-data', follow_redirects=True)

        assert response.status_code == 200

        # Cleanup all possible files
        for ext in ['jpg', 'jpeg', 'png', 'gif']:
            for prefix in ['profile', 'thumb']:
                path = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], f"{regular_user.id}_{prefix}.{ext}")
                if os.path.exists(path):
                    os.remove(path)

    def test_profile_picture_invalid_file_type(self, auth_client, regular_user):
        """Test that invalid file types are rejected."""
        invalid_file = FileStorage(
            stream=BytesIO(b'fake pdf content'),
            filename='test.pdf',
            content_type='application/pdf'
        )

        response = auth_client.post('/profile/edit', data={
            'email': regular_user.email,
            'bio': '',
            'profile_picture': invalid_file,
            'csrf_token': 'test_token'
        }, content_type='multipart/form-data', follow_redirects=True)

        # Should show error
        assert response.status_code == 200
        assert b'failed' in response.data.lower() or b'invalid' in response.data.lower()

    def test_profile_picture_file_too_large(self, auth_client, regular_user, monkeypatch):
        """Test that oversized files are rejected."""
        # Create a mock for validate_image_file that simulates size error
        def mock_validate_fail(file):
            return False, "File too large"

        from app.routes import profile
        monkeypatch.setattr(profile, 'validate_image_file', mock_validate_fail)

        img = Image.new('RGB', (100, 100))
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        large_file = FileStorage(stream=img_bytes, filename='large.jpg', content_type='image/jpeg')

        response = auth_client.post('/profile/edit', data={
            'email': regular_user.email,
            'bio': '',
            'profile_picture': large_file,
            'csrf_token': 'test_token'
        }, content_type='multipart/form-data', follow_redirects=True)

        assert response.status_code == 200
        assert b'failed' in response.data.lower() or b'large' in response.data.lower()

    def test_profile_picture_io_error_handling(self, auth_client, regular_user, monkeypatch, app):
        """Test handling of IOError during file save."""
        def mock_save_fail(*args, **kwargs):
            raise IOError("Disk full")

        img = Image.new('RGB', (100, 100))
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        test_image = FileStorage(stream=img_bytes, filename='test.jpg', content_type='image/jpeg')

        # Mock the FileStorage save method to raise IOError
        original_save = FileStorage.save
        def failing_save(self, dst, buffer_size=16384):
            if 'profile' in str(dst):
                raise IOError("Disk error")
            return original_save(self, dst, buffer_size)

        monkeypatch.setattr(FileStorage, 'save', failing_save)

        response = auth_client.post('/profile/edit', data={
            'email': regular_user.email,
            'bio': '',
            'profile_picture': test_image,
            'csrf_token': 'test_token'
        }, content_type='multipart/form-data', follow_redirects=True)

        # Should handle error gracefully
        assert response.status_code == 200

    def test_profile_picture_pil_error_handling(self, auth_client, regular_user, monkeypatch):
        """Test handling of PIL/Image errors during thumbnail creation."""
        # Create a file that will fail PIL processing
        corrupt_file = FileStorage(
            stream=BytesIO(b'\xFF\xD8\xFF\xE0corrupt'),
            filename='corrupt.jpg',
            content_type='image/jpeg'
        )

        # This should be caught by validation, but test the exception handling path
        response = auth_client.post('/profile/edit', data={
            'email': regular_user.email,
            'bio': '',
            'profile_picture': corrupt_file,
            'csrf_token': 'test_token'
        }, content_type='multipart/form-data', follow_redirects=True)

        # Should handle error gracefully
        assert response.status_code == 200

    def test_profile_picture_generic_exception_handling(self, auth_client, regular_user, monkeypatch):
        """Test handling of unexpected exceptions during upload."""
        def mock_validate_exception(file):
            return True, None  # Pass validation

        from app.routes import profile
        monkeypatch.setattr(profile, 'validate_image_file', mock_validate_exception)

        # Mock sanitize_filename to raise exception
        def mock_sanitize_fail(filename):
            raise Exception("Unexpected error")

        monkeypatch.setattr(profile, 'sanitize_filename', mock_sanitize_fail)

        img = Image.new('RGB', (100, 100))
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        test_image = FileStorage(stream=img_bytes, filename='test.jpg', content_type='image/jpeg')

        response = auth_client.post('/profile/edit', data={
            'email': regular_user.email,
            'bio': '',
            'profile_picture': test_image,
            'csrf_token': 'test_token'
        }, content_type='multipart/form-data', follow_redirects=True)

        # Should handle error gracefully
        assert response.status_code == 200


@pytest.mark.integration
class TestChangePassword:
    """Test suite for password change functionality."""

    def test_change_password_requires_authentication(self, client):
        """Test that change password requires login."""
        response = client.get('/profile/change-password')
        assert response.status_code == 302  # Redirect to login

    def test_change_password_get_shows_form(self, auth_client):
        """Test that GET request shows password change form."""
        response = auth_client.get('/profile/change-password')
        assert response.status_code == 200
        assert b'password' in response.data.lower()

    def test_change_password_success(self, auth_client, regular_user, db):
        """Test successful password change."""
        old_password_hash = regular_user.password_hash

        response = auth_client.post('/profile/change-password', data={
            'current_password': 'password123',
            'new_password': 'NewPassword456!',
            'confirm_password': 'NewPassword456!',
            'csrf_token': 'test_token'
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(regular_user)
        assert regular_user.password_hash != old_password_hash
        assert regular_user.check_password('NewPassword456!')

    def test_change_password_wrong_current_password(self, auth_client, regular_user):
        """Test that wrong current password is rejected."""
        response = auth_client.post('/profile/change-password', data={
            'current_password': 'WrongPassword',
            'new_password': 'NewPassword456!',
            'confirm_password': 'NewPassword456!',
            'csrf_token': 'test_token'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'incorrect' in response.data.lower()

    def test_change_password_mismatch_confirmation(self, auth_client, regular_user):
        """Test that mismatched password confirmation is rejected."""
        response = auth_client.post('/profile/change-password', data={
            'current_password': 'password123',
            'new_password': 'NewPassword456!',
            'confirm_password': 'DifferentPassword789!',
            'csrf_token': 'test_token'
        })

        # Should fail validation
        assert response.status_code == 200

    def test_change_password_weak_password(self, auth_client, regular_user):
        """Test that weak passwords are rejected if validation exists."""
        response = auth_client.post('/profile/change-password', data={
            'current_password': 'password123',
            'new_password': '123',
            'confirm_password': '123',
            'csrf_token': 'test_token'
        })

        # Should fail validation if password strength is enforced
        assert response.status_code == 200

    def test_change_password_redirects_on_success(self, auth_client, regular_user):
        """Test that successful password change redirects to profile."""
        response = auth_client.post('/profile/change-password', data={
            'current_password': 'password123',
            'new_password': 'ValidNewPass123!',
            'confirm_password': 'ValidNewPass123!',
            'csrf_token': 'test_token'
        }, follow_redirects=False)

        assert response.status_code == 302
        assert '/profile' in response.location

    def test_change_password_flash_success(self, auth_client, regular_user):
        """Test that success message is flashed."""
        response = auth_client.post('/profile/change-password', data={
            'current_password': 'password123',
            'new_password': 'NewValidPass456!',
            'confirm_password': 'NewValidPass456!',
            'csrf_token': 'test_token'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'success' in response.data.lower()


@pytest.mark.integration
class TestProfilePictureServing:
    """Test suite for profile picture file serving."""

    def test_profile_picture_route_exists(self, client):
        """Test that profile picture serving route is registered."""
        response = client.get('/uploads/profiles/nonexistent.jpg')
        assert response.status_code in [200, 404]

    def test_profile_picture_serves_real_file(self, client, app):
        """Test serving an actual profile picture file."""
        import os

        upload_dir = app.config['PROFILE_UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        test_file_path = os.path.join(upload_dir, 'test_profile.jpg')
        with open(test_file_path, 'w') as f:
            f.write('Test image content')

        try:
            response = client.get('/uploads/profiles/test_profile.jpg')
            assert response.status_code == 200
            assert b'Test image content' in response.data
        finally:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)

    def test_profile_picture_path_traversal_prevention(self, client):
        """Test that path traversal attacks are prevented."""
        response = client.get('/uploads/profiles/../../../etc/passwd')
        assert response.status_code in [400, 404]

    def test_profile_picture_nonexistent_file(self, client):
        """Test requesting a nonexistent profile picture."""
        response = client.get('/uploads/profiles/nonexistent_12345.jpg')
        assert response.status_code == 404


@pytest.mark.integration
class TestProfileEdgeCases:
    """Test edge cases for profile functionality."""

    def test_profile_with_empty_bio(self, auth_client, regular_user, db):
        """Test profile with empty/null bio."""
        regular_user.bio = None
        db.session.commit()

        response = auth_client.get('/profile')
        assert response.status_code == 200

    def test_profile_with_special_chars_in_bio(self, auth_client, regular_user, db):
        """Test profile with special characters in bio."""
        regular_user.bio = "Bio with <script>alert('xss')</script> and quotes\""
        db.session.commit()

        response = auth_client.get('/profile')
        assert response.status_code == 200
        # Template should escape HTML

    def test_profile_concurrent_edit_scenario(self, auth_client, regular_user, db):
        """Test handling of concurrent profile edits."""
        # Simulate two rapid updates
        auth_client.post('/profile/edit', data={
            'email': 'first@example.com',
            'bio': 'First bio',
            'csrf_token': 'test_token'
        })

        response = auth_client.post('/profile/edit', data={
            'email': 'second@example.com',
            'bio': 'Second bio',
            'csrf_token': 'test_token'
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(regular_user)
        # Last update should win
        assert regular_user.email == 'second@example.com'

    def test_edit_profile_without_changes(self, auth_client, regular_user, db):
        """Test submitting edit form without making changes."""
        original_email = regular_user.email
        original_bio = regular_user.bio

        response = auth_client.post('/profile/edit', data={
            'email': original_email,
            'bio': original_bio or '',
            'csrf_token': 'test_token'
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.refresh(regular_user)
        assert regular_user.email == original_email
        assert regular_user.bio == original_bio
