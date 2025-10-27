from app import db


class MinecraftCommand(db.Model):
    __tablename__ = 'minecraft_commands'

    command_id = db.Column(db.Integer, primary_key=True)
    command_name = db.Column(db.String(20), nullable=True)
    # JSON field for command options and parameters
    # Expected structure: {'args': ['arg1', 'arg2', ...], 'flags': {...}, ...}
    # Example: {'args': ['player1', '100', '64', '-200']} for teleport command
    options = db.Column(db.JSON)

    def __repr__(self):
        return f'<MinecraftCommand {self.command_name}>'

    def to_dict(self):
        return {
            'command_id': self.command_id,
            'command_name': self.command_name,
            'options': self.options
        }
