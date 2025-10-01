#!/usr/bin/env python3
"""
Seed initial roles into the database.
Run this script once after creating the roles table.
"""

from app import create_app, db
from app.models import Role, User

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
                print(f"Created role: {role_data['name']}")
            else:
                print(f"Role already exists: {role_data['name']}")

        db.session.commit()
        print("\nRole seeding completed successfully!")

        # Assign admin role to user "abcd"
        user = User.query.filter_by(username='abcd').first()
        if user:
            admin_role = Role.query.filter_by(name='admin').first()
            if admin_role and admin_role not in user.roles:
                user.roles.append(admin_role)
                db.session.commit()
                print(f"\nAssigned 'admin' role to user 'abcd'")
            else:
                print(f"\nUser 'abcd' already has 'admin' role")
        else:
            print("\nWarning: User 'abcd' not found")

if __name__ == '__main__':
    seed_roles()
