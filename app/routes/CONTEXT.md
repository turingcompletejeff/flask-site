# Routes Architecture

## Overview
Modular route organization using Flask Blueprints. Each file represents a specific domain of routes.

## Route Modules
- `main.py`: Public, non-authenticated routes (home, index)
- `auth.py`: Authentication-related routes (login, logout, registration)
- `blogpost.py`: Blog-related routes (create, read, update, delete posts)
- `mc.py`: Minecraft server management routes
- `admin.py`: Administrative routes with strict access controls
- `health.py`: Service health check endpoints
- `profile.py`: User profile management routes

## Key Patterns
- All routes use @login_required where appropriate
- CSRF protection enabled globally
- Draft post routes have specialized access controls