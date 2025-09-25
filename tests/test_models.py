# ============================================
# tests/test_models.py
# ============================================

import pytest


class TestModels:
    """Test database models."""
    
    def test_user_password(self, app):
        """Test user password hashing."""
        from app.models import User
        
        with app.app_context():
            user = User(username='test', email='test@test.com')
            user.set_password('mypassword')
            
            assert user.check_password('mypassword')
            assert not user.check_password('wrongpassword')
            assert user.password_hash != 'mypassword'  # Should be hashed
    
    def test_blogpost_json_field(self, app):
        """Test BlogPost JSON field works."""
        from app import db
        from app.models import BlogPost
        
        with app.app_context():
            post = BlogPost(
                title='JSON Test',
                content='Testing JSON',
                themap={'test': 'data', 'nested': {'key': 'value'}}
            )
            db.session.add(post)
            db.session.commit()
            
            # Retrieve and verify
            retrieved = BlogPost.query.filter_by(title='JSON Test').first()
            assert retrieved.themap == {'test': 'data', 'nested': {'key': 'value'}}
    
    def test_minecraft_command_array(self, app):
        """Test MinecraftCommand ARRAY field works."""
        from app import db
        from app.models import MinecraftCommand
        
        with app.app_context():
            cmd = MinecraftCommand(
                command_name='test_command',
                options=['option1', 'option2', 'option3']
            )
            db.session.add(cmd)
            db.session.commit()
            
            # Retrieve and verify
            retrieved = MinecraftCommand.query.filter_by(command_name='test_command').first()
            assert retrieved.options == ['option1', 'option2', 'option3']
            assert len(retrieved.options) == 3
