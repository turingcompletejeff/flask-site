from app import db


class MinecraftCommand(db.Model):
    __tablename__ = 'minecraft_commands'

    command_id = db.Column(db.Integer, primary_key=True)
    command_name = db.Column(db.String(20), nullable=True)
    command = db.Column(db.String(100), nullable=True)  # Command text
    description = db.Column(db.String(200), nullable=True)  # Command description
    # JSON field for command options and parameters
    # Expected structure: {'args': ['arg1', 'arg2', ...], 'flags': {...}, ...}
    # Example: {'args': ['player1', '100', '64', '-200']} for teleport command
    options = db.Column(db.JSON)

    def __repr__(self):
        return f'<MinecraftCommand {self.command or self.command_name}>'

    def to_dict(self):
        return {
            'command_id': self.command_id,
            'command_name': self.command_name,
            'command': self.command,
            'description': self.description,
            'options': self.options
        }
