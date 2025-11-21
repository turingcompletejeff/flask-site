from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app import db


class MinecraftCommand(db.Model):
    __tablename__ = 'minecraft_commands'

    command_id = db.Column(db.Integer, primary_key=True)
    command_name = db.Column(db.String(20), nullable=True)
    # JSON field for command options and parameters
    # Expected structure: {'args': ['arg1', 'arg2', ...], 'flags': {...}, ...}
    # Example: {'args': ['player1', '100', '64', '-200']} for teleport command
    options = db.Column(db.JSON)

    def __repr__(self) -> str:
        return f'<MinecraftCommand {self.command_name}>'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'command_id': self.command_id,
            'command_name': self.command_name,
            'options': self.options
        }


class MinecraftLocation(db.Model):
    """
    Minecraft fast travel location model.

    Stores named locations with coordinates and optional images
    for quick teleportation on the Minecraft server.
    """
    __tablename__ = 'minecraft_locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Minecraft coordinates (Float to support fractional positions)
    position_x = db.Column(db.Float, nullable=False)
    position_y = db.Column(db.Float, nullable=False)
    position_z = db.Column(db.Float, nullable=False)

    # Images (matches BlogPost pattern)
    portrait = db.Column(db.Text, nullable=True)
    thumbnail = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    last_updated = db.Column(
        db.DateTime,
        nullable=True,
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Creator relationship
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_by = db.relationship('User', backref='minecraft_locations')

    def __repr__(self) -> str:
        """String representation of location."""
        return f'<MinecraftLocation {self.name}>'

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize location to dictionary for API responses.

        Returns:
            Dictionary containing all location data with nested position object.
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'position': {
                'x': self.position_x,
                'y': self.position_y,
                'z': self.position_z
            },
            'portrait': self.portrait,
            'thumbnail': self.thumbnail,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_by_id': self.created_by_id
        }

    def has_edits(self) -> bool:
        """
        Check if location has been edited after creation.

        Returns:
            True if last_updated is set, False otherwise.
        """
        return self.last_updated is not None
