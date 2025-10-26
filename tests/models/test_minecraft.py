"""
Unit tests for MinecraftCommand model.

Tests cover:
- MinecraftCommand creation
- JSON options field handling
- to_dict() method
- String representation
"""

import pytest
from app.models import MinecraftCommand


@pytest.mark.unit
class TestMinecraftCommand:
    """Test suite for MinecraftCommand model with JSON options field."""

    def test_minecraft_command_creation(self, db):
        """Test basic MinecraftCommand creation."""
        command = MinecraftCommand(
            command_name='give',
            options={'args': ['player1', 'diamond', '64']}
        )
        db.session.add(command)
        db.session.commit()

        assert command.command_id is not None
        assert command.command_name == 'give'
        assert command.options == {'args': ['player1', 'diamond', '64']}

    def test_minecraft_command_options_json(self, db):
        """Test that options field properly stores JSON data."""
        command = MinecraftCommand(
            command_name='tp',
            options={'args': ['player1', '100', '64', '-200']}
        )
        db.session.add(command)
        db.session.commit()

        # Retrieve and verify
        retrieved = MinecraftCommand.query.filter_by(command_name='tp').first()
        assert retrieved.options == {'args': ['player1', '100', '64', '-200']}
        assert len(retrieved.options['args']) == 4

    def test_minecraft_command_empty_options(self, db):
        """Test MinecraftCommand with empty options args."""
        command = MinecraftCommand(
            command_name='list',
            options={'args': []}
        )
        db.session.add(command)
        db.session.commit()

        retrieved = MinecraftCommand.query.filter_by(command_name='list').first()
        assert retrieved.options == {'args': []}

    def test_minecraft_command_to_dict(self, db):
        """Test to_dict method includes all fields."""
        command = MinecraftCommand(
            command_name='ban',
            options={'args': ['player1', 'griefing']}
        )
        db.session.add(command)
        db.session.commit()

        result = command.to_dict()
        assert 'command_id' in result
        assert result['command_name'] == 'ban'
        assert result['options'] == {'args': ['player1', 'griefing']}

    def test_minecraft_command_repr(self, db):
        """Test string representation of MinecraftCommand."""
        command = MinecraftCommand(command_name='kick')
        assert 'kick' in repr(command)
