from app import db
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import TypeDecorator, String


class StringArray(TypeDecorator):
    """Cross-database string array type: ARRAY for PostgreSQL, JSON for SQLite."""
    impl = db.JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(String(40)))
        else:
            return dialect.type_descriptor(db.JSON())


class MinecraftCommand(db.Model):
    __tablename__ = 'minecraft_commands'

    command_id = db.Column(db.Integer, primary_key=True)
    command_name = db.Column(db.String(20), nullable=True)
    options = db.Column(StringArray)

    def __repr__(self):
        return f'<BlogPost {self.command_name}>'

    def to_dict(self):
        return {
            'command_id': self.command_id,
            'command_name': self.command_name,
            'options': self.options
        }
