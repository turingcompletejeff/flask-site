#!/usr/bin/env python3
"""
Seed initial roles into the database.
Run this script once after creating the roles table.
"""

import logging
from app import create_app, db
from app.models import Role, User

# Configure logging for standalone script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def seed_roles():
    app = create_app()
    with app.app_context():
        roles_data = [
            {'name': 'admin', 'description': 'Full system access'},
            {'name': 'blogger', 'description': 'Can create, edit, delete blog posts'},
            {'name': 'minecrafter', 'description': 'Access to Minecraft server controls'}
        ]

        for role_data in roles_data:
            existing = Role.query.filter_by(name=role_data['name']).first()
            if not existing:
                role = Role(**role_data)
                db.session.add(role)
                logger.info(f"Created role: {role_data['name']}")
            else:
                logger.info(f"Role already exists: {role_data['name']}")

        db.session.commit()
        logger.info("Role seeding completed successfully!")

        # Assign admin role to user "abcd"
        user = User.query.filter_by(username='abcd').first()
        if user:
            admin_role = Role.query.filter_by(name='admin').first()
            if admin_role and admin_role not in user.roles:
                user.roles.append(admin_role)
                db.session.commit()
                logger.info("Assigned 'admin' role to user 'abcd'")
            else:
                logger.info("User 'abcd' already has 'admin' role")
        else:
            logger.warning("User 'abcd' not found")

if __name__ == '__main__':
    seed_roles()
