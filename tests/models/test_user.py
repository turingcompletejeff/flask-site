"""
Unit tests for User and Role models.

Tests cover:
- User model: password hashing, role checking, admin status, uniqueness
- Role model: creation, relationships, uniqueness, timestamps
"""

import pytest
from datetime import datetime
from app.models import User, Role


@pytest.mark.unit
class TestUser:
    """Test suite for User model."""

    def test_user_creation(self, db):
        """Test basic user creation."""
        user = User(username='newuser', email='new@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.password_hash is not None
        assert user.password_hash != 'testpass'  # Should be hashed

    def test_set_password(self, db):
        """Test password hashing."""
        user = User(username='testuser', email='test@example.com')
        user.set_password('mypassword')

        assert user.password_hash is not None
        assert user.password_hash != 'mypassword'
        assert len(user.password_hash) > 20  # Bcrypt hashes are long

    def test_check_password_success(self, regular_user):
        """Test password verification with correct password."""
        assert regular_user.check_password('password123') is True

    def test_check_password_failure(self, regular_user):
        """Test password verification with incorrect password."""
        assert regular_user.check_password('wrongpassword') is False

    def test_check_password_empty(self, regular_user):
        """Test password verification with empty password."""
        assert regular_user.check_password('') is False

    def test_has_role_true(self, blogger_user, blogger_role):
        """Test has_role returns True when user has the role."""
        assert blogger_user.has_role('blogger') is True

    def test_has_role_false(self, regular_user):
        """Test has_role returns False when user doesn't have the role."""
        assert regular_user.has_role('blogger') is False

    def test_has_role_nonexistent(self, regular_user):
        """Test has_role returns False for non-existent role."""
        assert regular_user.has_role('nonexistent_role') is False

    def test_has_any_role_true(self, blogger_user):
        """Test has_any_role returns True when user has at least one role."""
        assert blogger_user.has_any_role(['blogger', 'admin']) is True

    def test_has_any_role_false(self, regular_user):
        """Test has_any_role returns False when user has none of the roles."""
        assert regular_user.has_any_role(['blogger', 'admin']) is False

    def test_has_any_role_empty_list(self, blogger_user):
        """Test has_any_role returns False for empty role list."""
        assert blogger_user.has_any_role([]) is False

    def test_is_admin_true(self, admin_user):
        """Test is_admin returns True for admin user."""
        assert admin_user.is_admin() is True

    def test_is_admin_false(self, regular_user):
        """Test is_admin returns False for non-admin user."""
        assert regular_user.is_admin() is False

    def test_is_admin_false_for_blogger(self, blogger_user):
        """Test is_admin returns False for blogger user."""
        assert blogger_user.is_admin() is False

    def test_user_multiple_roles(self, db, admin_role, blogger_role):
        """Test user can have multiple roles."""
        user = User(username='multiuser', email='multi@example.com')
        user.set_password('password')
        user.roles.append(admin_role)
        user.roles.append(blogger_role)
        db.session.add(user)
        db.session.commit()

        assert user.has_role('admin') is True
        assert user.has_role('blogger') is True
        assert user.is_admin() is True
        assert len(user.roles) == 2

    def test_unique_username_constraint(self, db, regular_user):
        """Test that usernames must be unique."""
        duplicate_user = User(username='testuser', email='different@example.com')
        duplicate_user.set_password('password')
        db.session.add(duplicate_user)

        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db.session.commit()

    def test_unique_email_constraint(self, db, regular_user):
        """Test that emails must be unique."""
        duplicate_user = User(username='differentuser', email='test@example.com')
        duplicate_user.set_password('password')
        db.session.add(duplicate_user)

        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db.session.commit()

    def test_user_created_at_timestamp(self, regular_user):
        """Test that created_at timestamp is set automatically."""
        assert regular_user.created_at is not None
        assert isinstance(regular_user.created_at, datetime)


@pytest.mark.unit
class TestRole:
    """Test suite for Role model."""

    def test_role_creation(self, db):
        """Test basic role creation."""
        role = Role(name='moderator', description='Moderator role')
        db.session.add(role)
        db.session.commit()

        assert role.id is not None
        assert role.name == 'moderator'
        assert role.description == 'Moderator role'

    def test_role_unique_name_constraint(self, db, admin_role):
        """Test that role names must be unique."""
        duplicate_role = Role(name='admin', description='Another admin role')
        db.session.add(duplicate_role)

        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db.session.commit()

    def test_role_created_at_timestamp(self, admin_role):
        """Test that created_at timestamp is set automatically."""
        assert admin_role.created_at is not None
        assert isinstance(admin_role.created_at, datetime)

    def test_role_repr(self, admin_role):
        """Test __repr__ method."""
        assert repr(admin_role) == '<Role admin>'

    def test_role_user_relationship(self, db, admin_role):
        """Test many-to-many relationship between roles and users."""
        user = User(username='roletest', email='roletest@example.com')
        user.set_password('password')
        user.roles.append(admin_role)
        db.session.add(user)
        db.session.commit()

        # Test bidirectional relationship
        assert user in admin_role.assigned_users
        assert admin_role in user.roles

    def test_role_multiple_users(self, db, blogger_role):
        """Test that a role can be assigned to multiple users."""
        user1 = User(username='blogger1', email='blogger1@example.com')
        user1.set_password('password')
        user1.roles.append(blogger_role)

        user2 = User(username='blogger2', email='blogger2@example.com')
        user2.set_password('password')
        user2.roles.append(blogger_role)

        db.session.add_all([user1, user2])
        db.session.commit()

        assert len(blogger_role.assigned_users) == 2  # Only the users created in this test
        assert user1 in blogger_role.assigned_users
        assert user2 in blogger_role.assigned_users
