# TC-50 Test Plan: Minecraft Commands CRUD Widget

## 📋 Executive Summary

This document provides a comprehensive Test-Driven Development (TDD) test plan for TC-50: Minecraft Commands CRUD widget. All tests must be written **BEFORE** implementation begins, following TDD principles.

**Coverage Targets:**
- Routes: 90%+ coverage
- Critical paths (authentication, authorization, data integrity): 100% coverage
- Edge cases and error handling: 100% coverage

**Reference Pattern:** `tests/test_routes_admin_role_crud.py` (inline editing, AJAX validation)

---

## 🎯 Feature Overview

### Objectives
Add CRUD (Create, Read, Update, Delete) functionality for Minecraft commands with inline editing capability, following the established pattern from role management.

### Model Structure
```python
class MinecraftCommand(db.Model):
    __tablename__ = 'minecraft_commands'

    command_id = db.Column(db.Integer, primary_key=True)
    command_name = db.Column(db.String(20), nullable=True)  # Max 20 chars
    options = db.Column(db.JSON)  # JSON field for flexibility
```

### Authorization Requirements
From `app/routes/mc.py` `before_request`:
- Must be authenticated
- Must have **minecrafter** role OR **admin** role
- Returns 403 Forbidden otherwise

### Planned Routes
Based on sprint plan (lines 302-381):
1. **GET /mc/commands** - List all commands (read-only display)
2. **POST /mc/commands/create** - Create new command (AJAX JSON)
3. **POST /mc/commands/<id>/update** - Update command inline (AJAX JSON)
4. **POST /mc/commands/<id>/delete** - Delete command

---

## 📁 Test File Structure

### Primary Test File
**Path:** `/home/shades/git/flask-site/tests/test_routes_mc_commands_crud.py`

**Structure:**
```python
"""
Tests for Minecraft commands CRUD operations (TC-50).

Tests cover:
- GET /mc/commands - List commands widget
- POST /mc/commands/create - Create new command via AJAX (JSON)
- POST /mc/commands/<id>/update - AJAX in-line command update
- POST /mc/commands/<id>/delete - Delete command
- Authentication and authorization requirements
- JSON validation (command_name length, options JSON format)
- Command name uniqueness and constraints
"""

import pytest
import json
from flask import url_for
from app.models import MinecraftCommand
from app import db


class TestCommandListView:
    """Tests for GET /mc/commands - viewing commands."""

class TestCommandCreation:
    """Tests for creating commands via AJAX."""

class TestInlineCommandUpdate:
    """Tests for AJAX in-line command update endpoint."""

class TestCommandDeletion:
    """Tests for deleting commands."""

class TestCommandValidation:
    """Tests for command_name and options JSON validation."""

class TestCommandAuthorization:
    """Tests for role-based access control (minecrafter/admin)."""
```

---

## 🔧 Required Fixtures

### New Fixtures to Add to `conftest.py`

#### 1. Minecrafter Role Fixture
```python
@pytest.fixture(scope='function')
def minecrafter_role(db):
    """Create and return a minecrafter role."""
    role = Role(name='minecrafter', description='Minecraft server management role')
    db.session.add(role)
    db.session.commit()
    return role
```

#### 2. Minecrafter User Fixture
```python
@pytest.fixture(scope='function')
def minecrafter_user(db, minecrafter_role):
    """
    Create and return a user with minecrafter role.

    Credentials:
        username: minecrafter
        password: mcpass123
        email: mc@example.com
    """
    user = User(username='minecrafter', email='mc@example.com')
    user.set_password('mcpass123')
    user.roles.append(minecrafter_role)
    db.session.add(user)
    db.session.commit()
    return user
```

#### 3. Minecrafter Client Fixture
```python
@pytest.fixture(scope='function')
def minecrafter_client(client, minecrafter_user):
    """
    Provide a test client authenticated as a minecrafter.

    Automatically logs in the minecrafter_user before test execution.
    """
    client.post('/login', data={
        'username': 'minecrafter',
        'password': 'mcpass123'
    }, follow_redirects=True)
    return client
```

#### 4. Minecraft Command Fixtures
```python
@pytest.fixture(scope='function')
def sample_command(db):
    """
    Create and return a sample Minecraft command.

    Attributes:
        command_name: teleport
        options: {'args': ['@p', '0', '64', '0']}
    """
    command = MinecraftCommand(
        command_name='teleport',
        options={'args': ['@p', '0', '64', '0']}
    )
    db.session.add(command)
    db.session.commit()
    return command


@pytest.fixture(scope='function')
def multiple_commands(db):
    """
    Create and return multiple Minecraft commands for list testing.

    Returns:
        list: List of 3 MinecraftCommand objects
    """
    commands = [
        MinecraftCommand(command_name='gamemode', options={'args': ['creative', '@p']}),
        MinecraftCommand(command_name='time', options={'args': ['set', 'day']}),
        MinecraftCommand(command_name='weather', options={'args': ['clear']})
    ]
    for cmd in commands:
        db.session.add(cmd)
    db.session.commit()
    return commands


@pytest.fixture(scope='function')
def command_with_empty_options(db):
    """
    Create a command with empty options for edge case testing.
    """
    command = MinecraftCommand(
        command_name='help',
        options={}
    )
    db.session.add(command)
    db.session.commit()
    return command
```

---

## 📝 Detailed Test Specifications

### Test Class 1: TestCommandListView

**Purpose:** Test GET /mc/commands route for displaying commands

#### Test 1.1: test_list_requires_authentication
```python
def test_list_requires_authentication(self, client, app):
    """Test unauthenticated access redirects to login."""
    # Arrange: No setup needed

    # Act
    with app.app_context():
        response = client.get(url_for('mc.manage_commands'))

    # Assert
    assert response.status_code == 302  # Redirect to login
    assert '/login' in response.location
```

**Coverage:** Authentication requirement
**Priority:** Critical (100% coverage requirement)

#### Test 1.2: test_list_regular_user_denied
```python
def test_list_regular_user_denied(self, auth_client, app):
    """Test regular user without minecrafter/admin role is denied."""
    # Arrange: auth_client is logged in as regular user (no roles)

    # Act
    with app.app_context():
        response = auth_client.get(url_for('mc.manage_commands'))

    # Assert
    assert response.status_code == 403  # Forbidden
```

**Coverage:** Authorization requirement (non-minecrafter/admin)
**Priority:** Critical

#### Test 1.3: test_list_minecrafter_success
```python
def test_list_minecrafter_success(self, minecrafter_client, multiple_commands, app):
    """Test minecrafter role can view commands list."""
    # Arrange: minecrafter_client logged in, 3 commands exist

    # Act
    with app.app_context():
        response = minecrafter_client.get(url_for('mc.manage_commands'))

    # Assert
    assert response.status_code == 200
    assert b'gamemode' in response.data
    assert b'time' in response.data
    assert b'weather' in response.data
```

**Coverage:** Minecrafter role access, command display
**Priority:** High

#### Test 1.4: test_list_admin_success
```python
def test_list_admin_success(self, admin_client, multiple_commands, app):
    """Test admin role can view commands list (admin bypass)."""
    # Arrange: admin_client logged in, 3 commands exist

    # Act
    with app.app_context():
        response = admin_client.get(url_for('mc.manage_commands'))

    # Assert
    assert response.status_code == 200
    assert b'gamemode' in response.data
```

**Coverage:** Admin role bypass
**Priority:** High

#### Test 1.5: test_list_empty_commands
```python
def test_list_empty_commands(self, minecrafter_client, app):
    """Test list view with no commands shows empty state."""
    # Arrange: No commands in database

    # Act
    with app.app_context():
        response = minecrafter_client.get(url_for('mc.manage_commands'))

    # Assert
    assert response.status_code == 200
    # Should show "No commands" or similar message
    assert b'No commands' in response.data or b'command' in response.data.lower()
```

**Coverage:** Empty state handling
**Priority:** Medium

---

### Test Class 2: TestCommandCreation

**Purpose:** Test POST /mc/commands/create route (AJAX JSON endpoint)

#### Test 2.1: test_create_requires_authentication
```python
def test_create_requires_authentication(self, client, app):
    """Test unauthenticated access is denied."""
    # Arrange
    data = {'command_name': 'test', 'options': {}}

    # Act
    with app.app_context():
        response = client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 302  # Redirect to login
```

**Coverage:** Authentication requirement
**Priority:** Critical

#### Test 2.2: test_create_regular_user_denied
```python
def test_create_regular_user_denied(self, auth_client, app):
    """Test regular user cannot create commands."""
    # Arrange
    data = {'command_name': 'test', 'options': {}}

    # Act
    with app.app_context():
        response = auth_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 403  # Forbidden
```

**Coverage:** Authorization requirement
**Priority:** Critical

#### Test 2.3: test_create_command_success_minecrafter
```python
def test_create_command_success_minecrafter(self, minecrafter_client, app):
    """Test successfully creating a new command as minecrafter."""
    # Arrange
    data = {
        'command_name': 'give',
        'options': {'args': ['@p', 'diamond', '64']}
    }

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 201
    response_data = response.get_json()
    assert response_data['status'] == 'success'
    assert response_data['command']['command_name'] == 'give'
    assert response_data['command']['options'] == {'args': ['@p', 'diamond', '64']}

    # Verify database
    command = MinecraftCommand.query.filter_by(command_name='give').first()
    assert command is not None
    assert command.options == {'args': ['@p', 'diamond', '64']}
```

**Coverage:** Successful creation with minecrafter role
**Priority:** Critical

#### Test 2.4: test_create_command_success_admin
```python
def test_create_command_success_admin(self, admin_client, app):
    """Test successfully creating a new command as admin."""
    # Arrange
    data = {
        'command_name': 'kill',
        'options': {'args': ['@e[type=zombie]']}
    }

    # Act
    with app.app_context():
        response = admin_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 201
    response_data = response.get_json()
    assert response_data['status'] == 'success'
    assert response_data['command']['command_name'] == 'kill'
```

**Coverage:** Admin role access
**Priority:** High

#### Test 2.5: test_create_command_empty_options
```python
def test_create_command_empty_options(self, minecrafter_client, app):
    """Test creating command with empty options object succeeds."""
    # Arrange
    data = {
        'command_name': 'help',
        'options': {}
    }

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 201
    response_data = response.get_json()
    assert response_data['command']['options'] == {}

    # Verify database
    command = MinecraftCommand.query.filter_by(command_name='help').first()
    assert command.options == {}
```

**Coverage:** Empty options edge case
**Priority:** Medium

#### Test 2.6: test_create_command_null_options
```python
def test_create_command_null_options(self, minecrafter_client, app):
    """Test creating command with null options succeeds."""
    # Arrange
    data = {
        'command_name': 'test',
        'options': None
    }

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 201
    response_data = response.get_json()
    assert response_data['command']['options'] is None
```

**Coverage:** Null options edge case (model allows nullable)
**Priority:** Medium

#### Test 2.7: test_create_command_name_too_long
```python
def test_create_command_name_too_long(self, minecrafter_client, app):
    """Test creating command with name exceeding 20 characters fails."""
    # Arrange
    data = {
        'command_name': 'a' * 21,  # 21 characters (max is 20)
        'options': {}
    }

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data['status'] == 'error'
    assert 'exceeds maximum length' in response_data['message'] or '20 characters' in response_data['message']
```

**Coverage:** Command name length validation
**Priority:** High

#### Test 2.8: test_create_command_empty_name
```python
def test_create_command_empty_name(self, minecrafter_client, app):
    """Test creating command with empty name fails."""
    # Arrange
    data = {
        'command_name': '',
        'options': {}
    }

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data['status'] == 'error'
    assert 'required' in response_data['message'].lower() or 'cannot be empty' in response_data['message'].lower()
```

**Coverage:** Empty name validation
**Priority:** High

#### Test 2.9: test_create_command_duplicate_name
```python
def test_create_command_duplicate_name(self, minecrafter_client, sample_command, app):
    """Test creating command with duplicate name fails."""
    # Arrange: sample_command has name 'teleport'
    data = {
        'command_name': 'teleport',  # Duplicate
        'options': {'args': ['different', 'args']}
    }

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data['status'] == 'error'
    assert 'already exists' in response_data['message']
```

**Coverage:** Duplicate name validation
**Priority:** High

#### Test 2.10: test_create_command_invalid_json_options
```python
def test_create_command_invalid_json_options(self, minecrafter_client, app):
    """Test creating command with non-dict/non-JSON options fails."""
    # Arrange
    data = {
        'command_name': 'test',
        'options': 'not-a-json-object'  # String instead of dict
    }

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data['status'] == 'error'
    assert 'invalid' in response_data['message'].lower() or 'must be' in response_data['message'].lower()
```

**Coverage:** Options type validation
**Priority:** Medium

#### Test 2.11: test_create_command_missing_data
```python
def test_create_command_missing_data(self, minecrafter_client, app):
    """Test creating command without required fields fails."""
    # Arrange: Missing command_name
    data = {
        'options': {}
    }

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data['status'] == 'error'
    assert 'Missing required fields' in response_data['message'] or 'command_name' in response_data['message']
```

**Coverage:** Missing required field validation
**Priority:** High

#### Test 2.12: test_create_command_no_json_data
```python
def test_create_command_no_json_data(self, minecrafter_client, app):
    """Test creating command with empty JSON fails."""
    # Arrange
    data = {}

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data['status'] == 'error'
    assert 'No data provided' in response_data['message'] or 'Missing required' in response_data['message']
```

**Coverage:** Empty request body validation
**Priority:** High

---

### Test Class 3: TestInlineCommandUpdate

**Purpose:** Test POST /mc/commands/<id>/update route (AJAX JSON endpoint)

#### Test 3.1: test_update_requires_authentication
```python
def test_update_requires_authentication(self, client, app):
    """Test unauthenticated access is denied."""
    # Arrange
    data = {'command_name': 'updated', 'options': {}}

    # Act
    with app.app_context():
        response = client.post(
            url_for('mc.update_command', command_id=1),
            json=data
        )

    # Assert
    assert response.status_code == 302  # Redirect to login
```

**Coverage:** Authentication requirement
**Priority:** Critical

#### Test 3.2: test_update_regular_user_denied
```python
def test_update_regular_user_denied(self, auth_client, sample_command, app):
    """Test regular user cannot update commands."""
    # Arrange
    data = {'command_name': 'updated', 'options': {}}

    # Act
    with app.app_context():
        response = auth_client.post(
            url_for('mc.update_command', command_id=sample_command.command_id),
            json=data
        )

    # Assert
    assert response.status_code == 403  # Forbidden
```

**Coverage:** Authorization requirement
**Priority:** Critical

#### Test 3.3: test_update_command_success
```python
def test_update_command_success(self, minecrafter_client, app):
    """Test successfully updating a command via AJAX."""
    # Arrange: Create command to update
    with app.app_context():
        command = MinecraftCommand(command_name='old_name', options={'args': ['old']})
        db.session.add(command)
        db.session.commit()
        command_id = command.command_id

        # Act: Update command
        response = minecrafter_client.post(
            url_for('mc.update_command', command_id=command_id),
            json={
                'command_name': 'new_name',
                'options': {'args': ['new', 'args']}
            },
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['command']['command_name'] == 'new_name'
        assert data['command']['options'] == {'args': ['new', 'args']}

        # Verify database was updated
        updated_command = MinecraftCommand.query.get(command_id)
        assert updated_command.command_name == 'new_name'
        assert updated_command.options == {'args': ['new', 'args']}
```

**Coverage:** Successful update
**Priority:** Critical

#### Test 3.4: test_update_command_clear_options
```python
def test_update_command_clear_options(self, minecrafter_client, sample_command, app):
    """Test updating command to have null options."""
    # Arrange: sample_command has options

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.update_command', command_id=sample_command.command_id),
            json={
                'command_name': sample_command.command_name,
                'options': None
            },
            content_type='application/json'
        )

        # Assert
        assert response.status_code == 200
        updated_command = MinecraftCommand.query.get(sample_command.command_id)
        assert updated_command.options is None
```

**Coverage:** Clearing options to null
**Priority:** Medium

#### Test 3.5: test_update_command_nonexistent
```python
def test_update_command_nonexistent(self, minecrafter_client, app):
    """Test updating non-existent command returns 404."""
    # Arrange
    data = {
        'command_name': 'test',
        'options': {}
    }

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.update_command', command_id=9999),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 404
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'not found' in data['message'].lower()
```

**Coverage:** Non-existent ID handling
**Priority:** High

#### Test 3.6: test_update_command_duplicate_name
```python
def test_update_command_duplicate_name(self, minecrafter_client, multiple_commands, app):
    """Test updating command to duplicate name fails."""
    # Arrange: multiple_commands[0] is 'gamemode', multiple_commands[1] is 'time'

    # Act: Try to rename 'gamemode' to 'time'
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.update_command', command_id=multiple_commands[0].command_id),
            json={
                'command_name': 'time',  # Duplicate of multiple_commands[1]
                'options': {}
            },
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'already exists' in data['message']
```

**Coverage:** Duplicate name on update
**Priority:** High

#### Test 3.7: test_update_command_name_too_long
```python
def test_update_command_name_too_long(self, minecrafter_client, sample_command, app):
    """Test updating command with name too long fails."""
    # Arrange

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.update_command', command_id=sample_command.command_id),
            json={
                'command_name': 'a' * 21,  # Too long
                'options': {}
            },
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert '20 characters' in data['message'] or 'maximum length' in data['message']
```

**Coverage:** Name length validation on update
**Priority:** High

#### Test 3.8: test_update_command_missing_data
```python
def test_update_command_missing_data(self, minecrafter_client, sample_command, app):
    """Test update fails with missing required fields."""
    # Arrange: Missing command_name

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.update_command', command_id=sample_command.command_id),
            json={'options': {}},  # Missing command_name
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Missing required fields' in data['message']
```

**Coverage:** Missing required field validation
**Priority:** High

#### Test 3.9: test_update_command_no_json_data
```python
def test_update_command_no_json_data(self, minecrafter_client, sample_command, app):
    """Test update fails when empty JSON data provided."""
    # Arrange

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.update_command', command_id=sample_command.command_id),
            json={},
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'No data provided' in data['message']
```

**Coverage:** Empty request body validation
**Priority:** High

---

### Test Class 4: TestCommandDeletion

**Purpose:** Test POST /mc/commands/<id>/delete route

#### Test 4.1: test_delete_requires_authentication
```python
def test_delete_requires_authentication(self, client, sample_command, app):
    """Test unauthenticated access is denied."""
    # Arrange

    # Act
    with app.app_context():
        response = client.post(
            url_for('mc.delete_command', command_id=sample_command.command_id),
            follow_redirects=False
        )

    # Assert
    assert response.status_code == 302  # Redirect to login
```

**Coverage:** Authentication requirement
**Priority:** Critical

#### Test 4.2: test_delete_regular_user_denied
```python
def test_delete_regular_user_denied(self, auth_client, sample_command, app):
    """Test regular user cannot delete commands."""
    # Arrange

    # Act
    with app.app_context():
        response = auth_client.post(
            url_for('mc.delete_command', command_id=sample_command.command_id),
            follow_redirects=False
        )

    # Assert
    assert response.status_code == 403  # Forbidden
```

**Coverage:** Authorization requirement
**Priority:** Critical

#### Test 4.3: test_delete_command_success
```python
def test_delete_command_success(self, minecrafter_client, app):
    """Test successfully deleting a command."""
    # Arrange: Create command to delete
    with app.app_context():
        command = MinecraftCommand(command_name='temporary', options={})
        db.session.add(command)
        db.session.commit()
        command_id = command.command_id

        # Act
        response = minecrafter_client.post(
            url_for('mc.delete_command', command_id=command_id),
            follow_redirects=True
        )

        # Assert
        assert response.status_code == 200

        # Check command was deleted
        deleted_command = MinecraftCommand.query.get(command_id)
        assert deleted_command is None
```

**Coverage:** Successful deletion
**Priority:** Critical

#### Test 4.4: test_delete_command_admin_success
```python
def test_delete_command_admin_success(self, admin_client, sample_command, app):
    """Test admin can delete commands."""
    # Arrange

    # Act
    with app.app_context():
        command_id = sample_command.command_id
        response = admin_client.post(
            url_for('mc.delete_command', command_id=command_id),
            follow_redirects=True
        )

        # Assert
        assert response.status_code == 200
        deleted_command = MinecraftCommand.query.get(command_id)
        assert deleted_command is None
```

**Coverage:** Admin role access
**Priority:** High

#### Test 4.5: test_delete_command_nonexistent
```python
def test_delete_command_nonexistent(self, minecrafter_client, app):
    """Test deleting non-existent command returns 404."""
    # Arrange

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.delete_command', command_id=9999)
        )

    # Assert
    assert response.status_code == 404
```

**Coverage:** Non-existent ID handling
**Priority:** High

---

### Test Class 5: TestCommandValidation

**Purpose:** Test validation logic for command data

#### Test 5.1: test_command_name_max_length_exactly_20
```python
def test_command_name_max_length_exactly_20(self, minecrafter_client, app):
    """Test command name with exactly 20 characters is accepted."""
    # Arrange
    data = {
        'command_name': 'a' * 20,  # Exactly 20 chars
        'options': {}
    }

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 201
    command = MinecraftCommand.query.filter_by(command_name='a' * 20).first()
    assert command is not None
```

**Coverage:** Boundary testing (max length)
**Priority:** Medium

#### Test 5.2: test_options_complex_json_structure
```python
def test_options_complex_json_structure(self, minecrafter_client, app):
    """Test complex nested JSON structure in options."""
    # Arrange
    data = {
        'command_name': 'complex',
        'options': {
            'args': ['@p', 'item'],
            'flags': {
                'silent': True,
                'count': 64
            },
            'metadata': {
                'author': 'admin',
                'tags': ['utility', 'player']
            }
        }
    }

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 201
    command = MinecraftCommand.query.filter_by(command_name='complex').first()
    assert command.options['flags']['silent'] is True
    assert command.options['metadata']['tags'] == ['utility', 'player']
```

**Coverage:** Complex JSON handling
**Priority:** Medium

#### Test 5.3: test_options_array_of_objects
```python
def test_options_array_of_objects(self, minecrafter_client, app):
    """Test options as array of objects."""
    # Arrange
    data = {
        'command_name': 'multi',
        'options': {
            'commands': [
                {'action': 'give', 'target': '@p'},
                {'action': 'teleport', 'coords': [0, 64, 0]}
            ]
        }
    }

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    assert response.status_code == 201
    command = MinecraftCommand.query.filter_by(command_name='multi').first()
    assert len(command.options['commands']) == 2
```

**Coverage:** Array of objects in options
**Priority:** Low

#### Test 5.4: test_command_name_case_sensitivity
```python
def test_command_name_case_sensitivity(self, minecrafter_client, sample_command, app):
    """Test command names are case-sensitive for uniqueness."""
    # Arrange: sample_command has name 'teleport'
    data = {
        'command_name': 'Teleport',  # Different case
        'options': {}
    }

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    # Should succeed (case-sensitive, so 'Teleport' != 'teleport')
    assert response.status_code == 201
```

**Coverage:** Case sensitivity
**Priority:** Low

#### Test 5.5: test_command_name_special_characters
```python
def test_command_name_special_characters(self, minecrafter_client, app):
    """Test command name with special characters."""
    # Arrange
    data = {
        'command_name': 'cmd-with_special',  # Dash and underscore
        'options': {}
    }

    # Act
    with app.app_context():
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json=data,
            content_type='application/json'
        )

    # Assert
    # Should succeed (no restrictions on special chars in spec)
    assert response.status_code == 201
```

**Coverage:** Special character handling
**Priority:** Low

---

### Test Class 6: TestCommandAuthorization

**Purpose:** Comprehensive authorization testing

#### Test 6.1: test_all_routes_require_authentication
```python
def test_all_routes_require_authentication(self, client, app):
    """Test all MC command routes require authentication."""
    # Arrange
    routes = [
        ('mc.manage_commands', {}, 'GET'),
        ('mc.create_command', {}, 'POST'),
        ('mc.update_command', {'command_id': 1}, 'POST'),
        ('mc.delete_command', {'command_id': 1}, 'POST')
    ]

    # Act & Assert
    with app.app_context():
        for route_name, kwargs, method in routes:
            if method == 'GET':
                response = client.get(url_for(route_name, **kwargs))
            else:
                response = client.post(url_for(route_name, **kwargs))

            assert response.status_code == 302, f"{route_name} should redirect unauthenticated"
```

**Coverage:** Global authentication requirement
**Priority:** Critical

#### Test 6.2: test_all_routes_deny_regular_user
```python
def test_all_routes_deny_regular_user(self, auth_client, sample_command, app):
    """Test all MC command routes deny regular users."""
    # Arrange
    routes = [
        ('mc.manage_commands', {}, 'GET'),
        ('mc.create_command', {}, 'POST'),
        ('mc.update_command', {'command_id': sample_command.command_id}, 'POST'),
        ('mc.delete_command', {'command_id': sample_command.command_id}, 'POST')
    ]

    # Act & Assert
    with app.app_context():
        for route_name, kwargs, method in routes:
            if method == 'GET':
                response = auth_client.get(url_for(route_name, **kwargs))
            else:
                response = auth_client.post(
                    url_for(route_name, **kwargs),
                    json={'command_name': 'test', 'options': {}},
                    content_type='application/json'
                )

            assert response.status_code == 403, f"{route_name} should deny regular user"
```

**Coverage:** Authorization enforcement across all routes
**Priority:** Critical

#### Test 6.3: test_minecrafter_role_access_all_routes
```python
def test_minecrafter_role_access_all_routes(self, minecrafter_client, app):
    """Test minecrafter role has access to all command routes."""
    # Arrange: Create command for update/delete tests
    with app.app_context():
        command = MinecraftCommand(command_name='test', options={})
        db.session.add(command)
        db.session.commit()
        command_id = command.command_id

        # Act & Assert
        # List
        response = minecrafter_client.get(url_for('mc.manage_commands'))
        assert response.status_code == 200

        # Create
        response = minecrafter_client.post(
            url_for('mc.create_command'),
            json={'command_name': 'new', 'options': {}},
            content_type='application/json'
        )
        assert response.status_code == 201

        # Update
        response = minecrafter_client.post(
            url_for('mc.update_command', command_id=command_id),
            json={'command_name': 'updated', 'options': {}},
            content_type='application/json'
        )
        assert response.status_code == 200

        # Delete
        response = minecrafter_client.post(
            url_for('mc.delete_command', command_id=command_id)
        )
        assert response.status_code == 200 or response.status_code == 302
```

**Coverage:** Minecrafter role full access
**Priority:** Critical

#### Test 6.4: test_admin_role_access_all_routes
```python
def test_admin_role_access_all_routes(self, admin_client, app):
    """Test admin role has access to all command routes (bypass)."""
    # Arrange: Create command for update/delete tests
    with app.app_context():
        command = MinecraftCommand(command_name='test_admin', options={})
        db.session.add(command)
        db.session.commit()
        command_id = command.command_id

        # Act & Assert
        # List
        response = admin_client.get(url_for('mc.manage_commands'))
        assert response.status_code == 200

        # Create
        response = admin_client.post(
            url_for('mc.create_command'),
            json={'command_name': 'admin_new', 'options': {}},
            content_type='application/json'
        )
        assert response.status_code == 201

        # Update
        response = admin_client.post(
            url_for('mc.update_command', command_id=command_id),
            json={'command_name': 'admin_updated', 'options': {}},
            content_type='application/json'
        )
        assert response.status_code == 200

        # Delete
        response = admin_client.post(
            url_for('mc.delete_command', command_id=command_id)
        )
        assert response.status_code == 200 or response.status_code == 302
```

**Coverage:** Admin role bypass
**Priority:** Critical

---

## 📊 Coverage Targets

### Per Route Coverage

| Route | Target Coverage | Critical Tests | Total Tests |
|-------|----------------|----------------|-------------|
| GET /mc/commands | 90% | 3 | 5 |
| POST /mc/commands/create | 95% | 8 | 12 |
| POST /mc/commands/<id>/update | 95% | 7 | 9 |
| POST /mc/commands/<id>/delete | 90% | 4 | 5 |
| Authorization (all routes) | 100% | 4 | 4 |

### Overall Coverage Goals

- **Authentication/Authorization:** 100% (all routes, all roles)
- **CRUD Operations:** 95% (success, failure, edge cases)
- **Data Validation:** 90% (name length, options format, duplicates)
- **Error Handling:** 90% (404, 400, 403, missing data)
- **Edge Cases:** 80% (empty options, null values, boundary conditions)

---

## 🎯 Test Execution Plan

### Phase 1: Foundation (Run First)
1. Add new fixtures to `conftest.py` (minecrafter_role, minecrafter_user, minecrafter_client, command fixtures)
2. Create test file skeleton with all test classes
3. Run empty test file to verify imports and fixtures

### Phase 2: Critical Path (Must Pass Before Implementation)
1. Authentication tests (all classes)
2. Authorization tests (TestCommandAuthorization)
3. Basic CRUD success tests (one per class)

### Phase 3: Validation (Core Business Logic)
1. Command name validation tests
2. Options validation tests
3. Duplicate name tests
4. Missing/empty data tests

### Phase 4: Edge Cases (Coverage Completion)
1. Empty options tests
2. Null values tests
3. Complex JSON tests
4. Boundary condition tests

### Phase 5: Integration (End-to-End Scenarios)
1. Multi-step workflows (create, update, delete)
2. Admin vs minecrafter role differences
3. List view with various data states

---

## 🚨 Edge Cases to Test

### Data Edge Cases
- ✅ Command name exactly 20 characters
- ✅ Command name 21 characters (should fail)
- ✅ Empty command name
- ✅ Null command name
- ✅ Empty options object `{}`
- ✅ Null options
- ✅ Complex nested JSON in options
- ✅ Array of objects in options
- ✅ Options as string (should fail)
- ✅ Options as array (may succeed depending on implementation)

### Authorization Edge Cases
- ✅ Unauthenticated access to all routes
- ✅ Regular user (no roles) access to all routes
- ✅ Minecrafter role access to all routes
- ✅ Admin role access to all routes (bypass)
- ✅ User with both minecrafter and admin roles

### Database Edge Cases
- ✅ Duplicate command names
- ✅ Case-sensitive name uniqueness
- ✅ Deleting non-existent command
- ✅ Updating non-existent command
- ✅ Creating command when database is empty
- ✅ Listing commands when database is empty

### Response Edge Cases
- ✅ Missing required fields in JSON
- ✅ Empty JSON body
- ✅ Malformed JSON (handled by Flask before route)
- ✅ Wrong content-type header

---

## ✅ Definition of Done

### Test File Completion Criteria
- [ ] All 35+ tests written and documented
- [ ] All fixtures added to `conftest.py`
- [ ] Test file passes linting (pytest --collect-only)
- [ ] All tests initially FAIL (red phase of TDD)
- [ ] Test names clearly describe what is being tested
- [ ] All tests follow Arrange-Act-Assert pattern
- [ ] Docstrings explain purpose of each test

### Coverage Criteria
- [ ] 100% coverage of authentication checks
- [ ] 100% coverage of authorization checks (minecrafter/admin)
- [ ] 95%+ coverage of CRUD operations
- [ ] 90%+ coverage of validation logic
- [ ] 90%+ coverage of error handling
- [ ] All edge cases have dedicated tests

### TDD Workflow Criteria
- [ ] Tests written BEFORE implementation
- [ ] All tests run and fail with appropriate error messages
- [ ] Test failures guide implementation decisions
- [ ] No implementation code written until tests are complete
- [ ] Tests can run independently and in any order
- [ ] Fixtures are reusable and minimal

---

## 📚 Implementation Notes

### When to Write Implementation
**DO NOT begin implementation until:**
1. This test plan is reviewed and approved
2. All fixtures are added to `conftest.py`
3. All test methods are written in `test_routes_mc_commands_crud.py`
4. All tests run and produce expected failures (red phase)
5. Coverage targets are agreed upon

### Test-First Development Flow
```
1. Write test → 2. Run test (fails) → 3. Write minimal code →
4. Run test (passes) → 5. Refactor → 6. Repeat
```

### Expected Test Failure Messages (Red Phase)
- `AttributeError: 'Blueprint' object has no attribute 'manage_commands'` → Route not implemented
- `KeyError: 'command'` → Response JSON structure not matching test expectations
- `AssertionError: 404 != 201` → Validation logic not implemented
- `IntegrityError: UNIQUE constraint failed` → Duplicate checking not implemented

---

## 🔍 Review Checklist

Before beginning implementation, verify:
- [ ] All test classes defined
- [ ] All 35+ test methods written with docstrings
- [ ] All fixtures added to `conftest.py`
- [ ] Test file imports successfully
- [ ] No syntax errors in test code
- [ ] Tests follow naming convention `test_<feature>_<scenario>`
- [ ] Critical tests identified and prioritized
- [ ] Edge cases comprehensively covered
- [ ] Authorization tests cover all role combinations
- [ ] Validation tests cover all constraints
- [ ] Error handling tests cover all error codes

---

## 📝 Summary

**Total Test Count:** 35 tests across 6 test classes

**Test Distribution:**
- TestCommandListView: 5 tests
- TestCommandCreation: 12 tests
- TestInlineCommandUpdate: 9 tests
- TestCommandDeletion: 5 tests
- TestCommandValidation: 5 tests (additional edge cases)
- TestCommandAuthorization: 4 tests (comprehensive role testing)

**New Fixtures Required:** 6
- `minecrafter_role`
- `minecrafter_user`
- `minecrafter_client`
- `sample_command`
- `multiple_commands`
- `command_with_empty_options`

**Coverage Targets:**
- Overall: 90%+
- Authentication/Authorization: 100%
- CRUD operations: 95%+
- Validation: 90%+

**Estimated Implementation Time (After Tests):** 1.5 - 2 hours
**Estimated Test Writing Time:** 2 - 2.5 hours

---

**Document Status:** ✅ Ready for Test Development
**Next Step:** Write all tests in `test_routes_mc_commands_crud.py` following this plan
