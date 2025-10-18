"""Convert MinecraftCommand options from array to JSON

Revision ID: tc51_options_json
Revises: 0197b862d1e3
Create Date: 2025-10-18 13:58:37

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = 'tc51_options_json'
down_revision = '0197b862d1e3'
branch_labels = None
depends_on = None


def upgrade():
    # Get database connection to perform data migration
    conn = op.get_bind()

    # For PostgreSQL: Convert ARRAY to JSON format
    # For SQLite: Already stored as JSON, just update structure
    dialect_name = conn.dialect.name

    if dialect_name == 'postgresql':
        # Step 1: Create a temporary column for the new JSON data
        op.add_column('minecraft_commands',
                     sa.Column('options_temp', sa.JSON(), nullable=True))

        # Step 2: Migrate data from array format to JSON format
        # Convert ['arg1', 'arg2'] to {'args': ['arg1', 'arg2']}
        conn.execute(text("""
            UPDATE minecraft_commands
            SET options_temp = jsonb_build_object('args',
                COALESCE(options, ARRAY[]::varchar[]))
            WHERE options_temp IS NULL
        """))

        # Step 3: Drop old column
        op.drop_column('minecraft_commands', 'options')

        # Step 4: Rename temp column to options
        op.alter_column('minecraft_commands', 'options_temp',
                       new_column_name='options')
    else:
        # SQLite: Data is already JSON, just update structure
        # Convert ['arg1', 'arg2'] to {'args': ['arg1', 'arg2']}
        with op.batch_alter_table('minecraft_commands', schema=None) as batch_op:
            # For SQLite, we need to handle this differently
            # Add temp column
            batch_op.add_column(sa.Column('options_temp', sa.JSON(), nullable=True))

        # Update data structure
        result = conn.execute(text("SELECT command_id, options FROM minecraft_commands"))
        for row in result:
            command_id = row[0]
            options = row[1]
            if options and isinstance(options, list):
                new_options = {'args': options}
                conn.execute(
                    text("UPDATE minecraft_commands SET options_temp = :opts WHERE command_id = :id"),
                    {"opts": str(new_options), "id": command_id}
                )

        with op.batch_alter_table('minecraft_commands', schema=None) as batch_op:
            batch_op.drop_column('options')
            batch_op.alter_column('options_temp', new_column_name='options')


def downgrade():
    # Get database connection
    conn = op.get_bind()
    dialect_name = conn.dialect.name

    if dialect_name == 'postgresql':
        # Step 1: Create temp array column
        op.add_column('minecraft_commands',
                     sa.Column('options_temp',
                              postgresql.ARRAY(sa.String(40)),
                              nullable=True))

        # Step 2: Convert JSON back to array
        # Convert {'args': ['arg1', 'arg2']} to ['arg1', 'arg2']
        conn.execute(text("""
            UPDATE minecraft_commands
            SET options_temp = ARRAY(
                SELECT jsonb_array_elements_text(options->'args')
            )
            WHERE options_temp IS NULL
        """))

        # Step 3: Drop JSON column
        op.drop_column('minecraft_commands', 'options')

        # Step 4: Rename temp to options
        op.alter_column('minecraft_commands', 'options_temp',
                       new_column_name='options')
    else:
        # SQLite: Convert back to array format
        with op.batch_alter_table('minecraft_commands', schema=None) as batch_op:
            batch_op.add_column(sa.Column('options_temp', sa.JSON(), nullable=True))

        result = conn.execute(text("SELECT command_id, options FROM minecraft_commands"))
        for row in result:
            command_id = row[0]
            options = row[1]
            if options and isinstance(options, dict) and 'args' in options:
                conn.execute(
                    text("UPDATE minecraft_commands SET options_temp = :opts WHERE command_id = :id"),
                    {"opts": str(options['args']), "id": command_id}
                )

        with op.batch_alter_table('minecraft_commands', schema=None) as batch_op:
            batch_op.drop_column('options')
            batch_op.alter_column('options_temp', new_column_name='options')
