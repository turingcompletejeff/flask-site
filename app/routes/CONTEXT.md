# Routes Architecture

## Overview
Modular route organization using Flask Blueprints. Each file represents a specific domain of routes.

## Route Modules
- `main.py`: Public, non-authenticated routes (home, index)
- `auth.py`: Authentication-related routes (login, logout, registration)
- `blogpost.py`: Blog-related routes (create, read, update, delete posts)
- `mc.py`: Minecraft server management routes
  - RCON command execution and player management
  - **Fast Travel Locations**: Full CRUD at `/mc/locations/*`
    - Coordinate validation (Y: -64 to 320)
    - Image upload handling (portrait + auto-generated thumbnail)
    - Creator-based authorization with admin override
- `admin.py`: Administrative routes with strict access controls
- `health.py`: Service health check endpoints
- `profile.py`: User profile management routes

## Routing Naming Standards

### Standard Pattern (RESTful-Inspired)
```
/resource                      # List/index (GET)
/resource/new                  # Create form + action (GET, POST)
/resource/<id>                 # View single resource (GET)
/resource/<id>/edit            # Edit form + action (GET, POST)
/resource/<id>/delete          # Delete action (POST)
/resource/<id>/<action>        # Specific resource actions (POST)
```

### Design Principles
1. **Resource-first naming**: Identify the resource before the action
2. **Include IDs for specific operations**: Always include resource ID when operating on a single entity
3. **Consistent verb placement**: Actions come after the resource identifier
4. **Plural nouns for collections**: Use `/users`, `/roles`, `/posts` for consistency
5. **Form-based POST methods**: Since this is not a REST API, use POST for all mutations

### Examples
```python
# Blog posts
/post                          # List all posts
/post/new                      # Create new post (GET form, POST action)
/post/<int:post_id>            # View specific post
/post/<int:post_id>/edit       # Edit post (GET form, POST action)
/post/<int:post_id>/delete     # Delete post (POST)

# Admin users
/admin/users                   # List users
/admin/users/create            # Create user (GET form, POST action)
/admin/users/<int:user_id>/edit            # Edit user
/admin/users/<int:user_id>/delete          # Delete user
/admin/users/<int:user_id>/toggle-role/<role_name>  # Toggle role

# Admin roles
/admin/roles                                # List roles
/admin/roles/create                         # Create role (POST)
/admin/roles/<int:role_id>/update           # Update role (POST)
/admin/roles/<int:role_id>/delete           # Delete role (POST)
```

## Key Patterns
- All routes use @login_required where appropriate
- CSRF protection enabled globally
- Draft post routes have specialized access controls
- Blueprint registration handled in `app/__init__.py`