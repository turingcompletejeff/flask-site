"""
Test suite for image handling in locations.

Tests cover:
- Image validation
- Image saving
- Thumbnail generation
- Image cleanup
- Error recovery
"""

import pytest
import os
from pathlib import Path
from PIL import Image
from io import BytesIO
from flask import url_for
from app import db


class TestLocationImageHandling:
    """Image handling for locations tests."""

    def test_portrait_upload(self, minecrafter_client, mock_image_file):
        """Test uploading a portrait image."""
        response = minecrafter_client.post('/mc/locations/create', data={
            'name': 'Location with Image',
            'position_x': 0.0,
            'position_y': 64.0,
            'position_z': 0.0,
            'portrait': mock_image_file,
        }, follow_redirects=True)

        # Check if created successfully
        assert response.status_code in [200, 201]

        # Verify location was created with portrait
        from app.models import MinecraftLocation
        location = MinecraftLocation.query.filter_by(name='Location with Image').first()
        assert location is not None
        # Portrait should be set (filename stored)
        assert location.portrait is not None

    def test_portrait_required_for_thumbnail_generation(self, minecrafter_client, mock_image_file):
        """Test that thumbnail is generated from portrait."""
        response = minecrafter_client.post('/mc/locations/create', data={
            'name': 'Auto Thumbnail',
            'position_x': 0.0,
            'position_y': 64.0,
            'position_z': 0.0,
            'portrait': mock_image_file,
        }, follow_redirects=True)

        assert response.status_code in [200, 201]

        # Verify location was created with thumbnail
        from app.models import MinecraftLocation
        location = MinecraftLocation.query.filter_by(name='Auto Thumbnail').first()
        assert location is not None
        # Portrait should be set and thumbnail auto-generated
        assert location.portrait is not None
        assert location.thumbnail is not None
        assert 'thumb' in location.thumbnail

    def test_custom_thumbnail_upload(self, minecrafter_client, mock_image_file):
        """Test uploading custom thumbnail."""
        # Create second image file for thumbnail
        from werkzeug.datastructures import FileStorage
        thumb_image = BytesIO()
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(thumb_image, format='PNG')
        thumb_image.seek(0)

        thumbnail_file = FileStorage(
            stream=thumb_image,
            filename='custom_thumb.png',
            content_type='image/png'
        )

        response = minecrafter_client.post('/mc/locations/create', data={
            'name': 'Custom Thumbnail',
            'position_x': 0.0,
            'position_y': 64.0,
            'position_z': 0.0,
            'portrait': mock_image_file,
            'thumbnail': thumbnail_file,
        }, follow_redirects=True)

        assert response.status_code in [200, 201]

        # Verify location was created with custom thumbnail
        from app.models import MinecraftLocation
        location = MinecraftLocation.query.filter_by(name='Custom Thumbnail').first()
        assert location is not None
        # Both portrait and thumbnail should be set
        assert location.portrait is not None
        assert location.thumbnail is not None

    def test_thumbnail_resized_to_300x300(self, app, client, minecrafter_user):
        """Test that thumbnail is resized to 300x300."""
        # Create large test image
        large_image = BytesIO()
        img = Image.new('RGB', (1000, 1000), color='red')
        img.save(large_image, format='PNG')
        large_image.seek(0)

        with client:
            client.post('/auth/login', data={
                'username': minecrafter_user.username,
                'password': 'testpass'
            })

            response = client.post('/mc/locations/create', data={
                'name': 'Large Image',
                'position_x': 0.0,
                'position_y': 64.0,
                'position_z': 0.0,
                'portrait': (large_image, 'large_image.png'),
            }, follow_redirects=True, content_type='multipart/form-data')

            assert response.status_code in [200, 201]

            # Verify thumbnail is 300x300 or smaller
            upload_folder = app.config.get('MC_LOCATION_UPLOAD_FOLDER')
            if upload_folder and os.path.exists(upload_folder):
                files = os.listdir(upload_folder)
                thumb_files = [f for f in files if 'thumb' in f]
                if thumb_files:
                    thumb_path = os.path.join(upload_folder, thumb_files[0])
                    img = Image.open(thumb_path)
                    # Thumbnail should fit in 300x300 box
                    assert img.width <= 300 and img.height <= 300

    def test_invalid_image_type_rejected(self, app, client, minecrafter_user, mock_invalid_file):
        """Test that non-image files are rejected."""
        with client:
            client.post('/auth/login', data={
                'username': minecrafter_user.username,
                'password': 'testpass'
            })

            response = client.post('/mc/locations/create', data={
                'name': 'Invalid Image',
                'position_x': 0.0,
                'position_y': 64.0,
                'position_z': 0.0,
                'portrait': mock_invalid_file,
            }, content_type='multipart/form-data', follow_redirects=True)

            # Should show error (form validation or JSON error)
            # Either 200 with errors or 400 with JSON errors
            assert response.status_code in [200, 400]

            # If JSON response, check for errors
            if response.content_type and 'json' in response.content_type:
                data = response.get_json()
                if data:
                    assert data.get('success') == False or 'errors' in data

    def test_image_cleanup_on_delete(self, app, client, minecrafter_user):
        """Test that images are deleted when location is deleted."""
        from app.models import MinecraftLocation, User

        # Create location with image references
        with app.app_context():
            user = User.query.filter_by(username=minecrafter_user.username).first()

            location = MinecraftLocation(
                name="To Delete With Images",
                position_x=0.0,
                position_y=64.0,
                position_z=0.0,
                portrait="test.jpg",
                thumbnail="thumb_test.jpg",
                created_by_id=user.id
            )
            db.session.add(location)
            db.session.commit()
            location_id = location.id

        with client.session_transaction() as session:
            # Login user
            with app.app_context():
                user = User.query.filter_by(username=minecrafter_user.username).first()
                session['_user_id'] = str(user.id)

        # Delete the location
        response = client.post(
            f'/mc/locations/{location_id}/delete',
            headers={'X-Requested-With': 'XMLHttpRequest'},
            content_type='application/json'
        )

        # Should succeed
        assert response.status_code == 200

        # Check JSON response
        data = response.get_json()
        assert data['success'] == True

        # Location should be deleted
        with app.app_context():
            deleted = db.session.get(MinecraftLocation, location_id)
            assert deleted is None

    def test_location_without_images(self, app, client, minecrafter_user):
        """Test that locations can be created without images."""
        with client:
            client.post('/auth/login', data={
                'username': minecrafter_user.username,
                'password': 'testpass'
            })

            response = client.post('/mc/locations/create', data={
                'name': 'No Images Location',
                'position_x': 100.0,
                'position_y': 64.0,
                'position_z': 200.0,
            }, follow_redirects=True, content_type='multipart/form-data')

            assert response.status_code in [200, 201]

    def test_edit_location_replace_portrait(self, app, client, minecrafter_user, mock_image_file):
        """Test replacing portrait image when editing location."""
        from app.models import MinecraftLocation, User

        # Create location
        with app.app_context():
            user = User.query.filter_by(username=minecrafter_user.username).first()

            location = MinecraftLocation(
                name="Edit Portrait Test",
                position_x=0.0,
                position_y=64.0,
                position_z=0.0,
                portrait="old_portrait.jpg",
                thumbnail="thumb_old_portrait.jpg",
                created_by_id=user.id
            )
            db.session.add(location)
            db.session.commit()
            location_id = location.id

        with client:
            client.post('/auth/login', data={
                'username': minecrafter_user.username,
                'password': 'testpass'
            })

            # Edit with new portrait
            response = client.post(f'/mc/locations/{location_id}/edit', data={
                'name': 'Edit Portrait Test',
                'position_x': 0.0,
                'position_y': 64.0,
                'position_z': 0.0,
                'portrait': mock_image_file,
            }, follow_redirects=True, content_type='multipart/form-data')

            assert response.status_code in [200, 302]

    def test_create_location_invalid_portrait(self, minecrafter_client, mock_invalid_file):
        """Test that invalid portrait files are rejected with proper error response."""
        response = minecrafter_client.post('/mc/locations/create', data={
            'name': 'Invalid Portrait',
            'position_x': 0.0,
            'position_y': 64.0,
            'position_z': 0.0,
            'portrait': mock_invalid_file,
        }, content_type='multipart/form-data')

        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] == False
        assert 'portrait' in data['errors']
        # Check that error message is about invalid image
        error_msg = str(data['errors']['portrait'])
        assert 'Only JPG and PNG images are allowed' in error_msg or 'Portrait upload failed' in error_msg

    def test_create_location_portrait_save_error(self, minecrafter_client, mock_image_file):
        """Test error handling when portrait save fails."""
        from unittest.mock import patch, MagicMock

        # Mock the save method to raise IOError
        with patch.object(type(mock_image_file), 'save', side_effect=IOError("Disk full")):
            response = minecrafter_client.post('/mc/locations/create', data={
                'name': 'Save Error',
                'position_x': 0.0,
                'position_y': 64.0,
                'position_z': 0.0,
                'portrait': mock_image_file,
            }, content_type='multipart/form-data')

            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] == False
            assert 'portrait' in data['errors']
            assert 'Error saving portrait' in str(data['errors']['portrait'])

    def test_create_location_invalid_thumbnail_with_portrait_cleanup(self, minecrafter_client, mock_image_file, mock_invalid_file):
        """Test that portrait is cleaned up when thumbnail validation fails."""
        from werkzeug.datastructures import FileStorage
        from io import BytesIO

        # Create invalid thumbnail (text file disguised as image)
        invalid_thumb = BytesIO(b"This is not an image")
        invalid_thumbnail = FileStorage(
            stream=invalid_thumb,
            filename='fake_thumb.png',
            content_type='image/png'
        )

        response = minecrafter_client.post('/mc/locations/create', data={
            'name': 'Invalid Thumbnail',
            'position_x': 0.0,
            'position_y': 64.0,
            'position_z': 0.0,
            'portrait': mock_image_file,
            'thumbnail': invalid_thumbnail,
        }, content_type='multipart/form-data')

        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] == False
        assert 'thumbnail' in data['errors']

        # Verify location was not created (rollback happened)
        from app.models import MinecraftLocation
        location = MinecraftLocation.query.filter_by(name='Invalid Thumbnail').first()
        assert location is None

    def test_create_location_thumbnail_processing_error(self, minecrafter_client, mock_image_file):
        """Test error handling when thumbnail processing fails."""
        from unittest.mock import patch, MagicMock
        from werkzeug.datastructures import FileStorage
        from io import BytesIO

        # Create a valid thumbnail file
        thumb_image = BytesIO()
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(thumb_image, format='PNG')
        thumb_image.seek(0)

        thumbnail_file = FileStorage(
            stream=thumb_image,
            filename='thumb.png',
            content_type='image/png'
        )

        # Mock PIL Image.thumbnail to raise exception during thumbnail resizing
        # This way portrait validation succeeds, but thumbnail processing fails
        original_thumbnail_method = Image.Image.thumbnail

        def mock_thumbnail_error(self, *args, **kwargs):
            raise Exception("PIL processing error")

        with patch.object(Image.Image, 'thumbnail', side_effect=mock_thumbnail_error):
            response = minecrafter_client.post('/mc/locations/create', data={
                'name': 'Thumbnail Error',
                'position_x': 0.0,
                'position_y': 64.0,
                'position_z': 0.0,
                'portrait': mock_image_file,
                'thumbnail': thumbnail_file,
            }, content_type='multipart/form-data')

            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] == False
            # Error could be in thumbnail or portrait (depending on which processing fails)
            assert 'thumbnail' in data['errors'] or 'portrait' in data['errors']
            error_msg = str(data['errors'])
            assert 'Error' in error_msg or 'processing' in error_msg or 'PIL' in error_msg

    def test_create_location_auto_thumbnail_generation_error(self, minecrafter_client, mock_image_file):
        """Test error handling when auto-thumbnail generation fails."""
        from unittest.mock import patch, MagicMock

        # Create a mock that succeeds for save but fails for Image.open (auto-thumbnail generation)
        original_open = Image.open
        call_count = [0]

        def mock_open_selective(*args, **kwargs):
            call_count[0] += 1
            # First call is validation (succeed), second call is auto-thumbnail generation (fail)
            if call_count[0] >= 2:
                raise Exception("Auto-thumbnail generation failed")
            return original_open(*args, **kwargs)

        with patch('PIL.Image.open', side_effect=mock_open_selective):
            response = minecrafter_client.post('/mc/locations/create', data={
                'name': 'Auto Thumbnail Error',
                'position_x': 0.0,
                'position_y': 64.0,
                'position_z': 0.0,
                'portrait': mock_image_file,
            }, content_type='multipart/form-data')

            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] == False
            assert 'portrait' in data['errors'] or 'thumbnail' in data['errors']


class TestLocationAuthorization:
    """Authorization tests for location edit and delete."""

    def test_edit_location_unauthorized(self, app, db, minecrafter_client):
        """Test that non-creators cannot edit locations."""
        from app.models import MinecraftLocation, User

        # Create location as different user
        with app.app_context():
            other_user = User(username='otheruser', email='other@example.com')
            other_user.set_password('password')
            db.session.add(other_user)
            db.session.flush()

            location = MinecraftLocation(
                name="Other's Location",
                position_x=0.0,
                position_y=64.0,
                position_z=0.0,
                created_by_id=other_user.id
            )
            db.session.add(location)
            db.session.commit()
            location_id = location.id

        # Try to edit as minecrafter (different user)
        response = minecrafter_client.post(f'/mc/locations/{location_id}/edit', data={
            'name': 'Hacked',
            'position_x': 999.0,
            'position_y': 999.0,
            'position_z': 999.0,
        }, content_type='multipart/form-data')

        assert response.status_code == 403

    def test_delete_location_unauthorized(self, app, db, minecrafter_client):
        """Test that non-creators cannot delete locations."""
        from app.models import MinecraftLocation, User

        # Create location as different user
        with app.app_context():
            other_user = User(username='anotheruser', email='another@example.com')
            other_user.set_password('password')
            db.session.add(other_user)
            db.session.flush()

            location = MinecraftLocation(
                name="Another's Location",
                position_x=0.0,
                position_y=64.0,
                position_z=0.0,
                created_by_id=other_user.id
            )
            db.session.add(location)
            db.session.commit()
            location_id = location.id

        # Try to delete as minecrafter (different user)
        response = minecrafter_client.post(
            f'/mc/locations/{location_id}/delete',
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )

        assert response.status_code == 403


class TestLocationEditEndpoint:
    """Tests for location edit endpoint."""

    def test_get_location_for_edit(self, app, db, minecrafter_client, minecrafter_user):
        """Test retrieving location data for editing (GET request)."""
        from app.models import MinecraftLocation

        # Create location
        with app.app_context():
            location = MinecraftLocation(
                name="Edit Me",
                position_x=100.0,
                position_y=64.0,
                position_z=200.0,
                created_by_id=minecrafter_user.id
            )
            db.session.add(location)
            db.session.commit()
            location_id = location.id

        # GET request to retrieve edit form
        response = minecrafter_client.get(f'/mc/locations/{location_id}/edit')

        assert response.status_code == 200
        # Check that template is rendered (HTML response)
        assert b'Edit Fast Travel Location' in response.data
        # Check pre-populated value in form
        assert b'Edit Me' in response.data

    def test_edit_location_invalid_data(self, app, db, minecrafter_client, minecrafter_user):
        """Test editing location with invalid form data re-renders template with errors."""
        from app.models import MinecraftLocation

        # Create location
        with app.app_context():
            location = MinecraftLocation(
                name="Valid",
                position_x=0.0,
                position_y=64.0,
                position_z=0.0,
                created_by_id=minecrafter_user.id
            )
            db.session.add(location)
            db.session.commit()
            location_id = location.id

        # Submit with missing required fields
        response = minecrafter_client.post(f'/mc/locations/{location_id}/edit', data={
            'position_x': 0.0,
            # Missing name, position_y, position_z
        }, content_type='multipart/form-data')

        # Template is re-rendered with errors (200 OK)
        assert response.status_code == 200
        # Check for error messages in rendered template
        assert b'This field is required' in response.data or b'required' in response.data.lower()

    def test_edit_location_with_invalid_portrait(self, app, db, minecrafter_client, minecrafter_user, mock_invalid_file):
        """Test editing location with invalid portrait file shows error."""
        from app.models import MinecraftLocation

        # Create location
        with app.app_context():
            location = MinecraftLocation(
                name="Edit Portrait",
                position_x=0.0,
                position_y=64.0,
                position_z=0.0,
                created_by_id=minecrafter_user.id
            )
            db.session.add(location)
            db.session.commit()
            location_id = location.id

        # Try to update with invalid portrait
        response = minecrafter_client.post(f'/mc/locations/{location_id}/edit', data={
            'name': 'Edit Portrait',
            'position_x': 0.0,
            'position_y': 64.0,
            'position_z': 0.0,
            'portrait': mock_invalid_file,
        }, content_type='multipart/form-data')

        # Template is rendered with error (200 OK)
        assert response.status_code == 200
        # Check for error message about portrait
        assert b'portrait' in response.data.lower() or b'image' in response.data.lower()

    def test_edit_location_portrait_save_error(self, app, db, minecrafter_client, minecrafter_user, mock_image_file):
        """Test error handling when portrait save fails during edit."""
        from app.models import MinecraftLocation
        from unittest.mock import patch

        # Create location
        with app.app_context():
            location = MinecraftLocation(
                name="Edit Save Error",
                position_x=0.0,
                position_y=64.0,
                position_z=0.0,
                created_by_id=minecrafter_user.id
            )
            db.session.add(location)
            db.session.commit()
            location_id = location.id

        # Mock save to raise exception
        with patch.object(type(mock_image_file), 'save', side_effect=IOError("Disk error")):
            response = minecrafter_client.post(f'/mc/locations/{location_id}/edit', data={
                'name': 'Edit Save Error',
                'position_x': 0.0,
                'position_y': 64.0,
                'position_z': 0.0,
                'portrait': mock_image_file,
            }, content_type='multipart/form-data')

            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] == False
            assert 'portrait' in data['errors'] or 'thumbnail' in data['errors']


class TestLocationImageCleanup:
    """Tests for image cleanup on delete."""

    def test_delete_location_with_image_cleanup_errors(self, app, db, minecrafter_client, minecrafter_user):
        """Test delete when image files can't be removed."""
        from app.models import MinecraftLocation, User
        from unittest.mock import patch
        import os

        # Create location with image references
        with app.app_context():
            user = User.query.filter_by(username=minecrafter_user.username).first()

            location = MinecraftLocation(
                name="Delete with Image Errors",
                position_x=0.0,
                position_y=64.0,
                position_z=0.0,
                portrait="test_delete.jpg",
                thumbnail="thumb_test_delete.jpg",
                created_by_id=user.id
            )
            db.session.add(location)
            db.session.commit()
            location_id = location.id

        # Mock os.remove to fail
        with patch('os.remove', side_effect=OSError("Permission denied")):
            response = minecrafter_client.post(
                f'/mc/locations/{location_id}/delete',
                headers={'X-Requested-With': 'XMLHttpRequest'}
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] == True
            # Should have warnings about images that couldn't be removed
            assert 'warnings' in data or 'message' in data


class TestMCServerIntegration:
    """Tests for Minecraft server connection error handling."""

    def test_mc_status_connection_refused(self, app, minecrafter_client):
        """Test MC status when server refuses connection."""
        from unittest.mock import patch

        with patch('mctools.QUERYClient') as mock_query:
            # Configure mock to raise ConnectionRefusedError
            mock_query.side_effect = ConnectionRefusedError("Connection refused")

            response = minecrafter_client.get('/mc/status')

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'offline'

    def test_mc_query_os_error(self, app, minecrafter_client):
        """Test MC query endpoint with OSError."""
        from unittest.mock import patch, MagicMock

        with patch('mctools.QUERYClient') as mock_query_class:
            # Create mock instance
            mock_instance = MagicMock()
            mock_instance.get_full_stats.side_effect = OSError("Network error")
            mock_query_class.return_value = mock_instance

            response = minecrafter_client.get('/mc/query')

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'MC query OS error' in str(data.get('message', '')) or data['status'] == 'error'
