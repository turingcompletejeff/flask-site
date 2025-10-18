# flask-site
Portfolio site to host a blog and my projects

## 📌 Features

- **Blog System**: Full CRUD blog posts with text, image, and HTML encoding support
- **User Authentication**: Registration and login system
- **Minecraft Integration**:
  - Connect to Minecraft servers via RCON
  - Send server commands
  - List connected players

## 📂 Project Structure

```
flask-site/
│
├── app/                    # Main application package
│   ├── __init__.py         # Flask application initialization and configuration
│   │
│   ├── models/             # Modular database models
│   │   ├── __init__.py     # Centralized model exports
│   │   ├── user.py         # User and Role models
│   │   ├── blog.py         # BlogPost model
│   │   └── minecraft.py    # MinecraftCommand model
│   │
│   ├── forms/              # Modular form definitions
│   │   ├── __init__.py     # Centralized form exports
│   │   ├── contact.py      # Contact form
│   │   ├── blog.py         # Blog post form
│   │   ├── profile.py      # Profile edit form
│   │   └── admin.py        # Admin forms
│   │
│   ├── routes/             # Modular route blueprints
│   │   ├── __init__.py     # Centralized route exports
│   │   ├── main.py         # Homepage and core routes
│   │   ├── auth.py         # Authentication routes
│   │   ├── blogpost.py     # Blog CRUD routes
│   │   ├── mc.py           # Minecraft server routes
│   │   ├── health.py       # Health check routes
│   │   ├── profile.py      # User profile routes
│   │   └── admin.py        # Admin panel routes
│   │
│   ├── utils/              # Utility modules and decorators
│   │   ├── __init__.py     # Centralized utility exports
│   │   ├── auth_decorators.py  # Role-based access decorators
│   │   ├── filters.py      # Jinja2 template filters
│   │   ├── file_validation.py  # File upload validation
│   │   └── image_utils.py  # Image processing utilities
│   │
│   ├── templates/          # HTML templates (Jinja2)
│   └── static/             # Static files (CSS, JavaScript, images)
│
├── uploads/                # File upload directory
├── config.py               # Application configuration
├── run.py                  # Application entry point
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## ⚙️ Installation (Unchanged)

[Previous installation instructions remain the same]

## 🛡️ Environment Configuration (Unchanged)

[Previous environment configuration remains the same]

## 🚀 Running the Application (Unchanged)

[Previous running instructions remain the same]

## 🔧 Key Components (Minor Update)

- **Authentication**: Modular user registration and login system
- **Blog Management**: Create, read, update, and delete blog posts
- **File Uploads**: Improved file handling with validation utilities
- **Minecraft Integration**: RCON-based server management
- **Responsive Design**: Mobile-friendly interface
- **Modular Architecture**: Improved code organization with directory-based separation of concerns

## 📝 Import Patterns (New Section)

### Importing from Modular Components

```python
# Models
from app.models import User, BlogPost, Role

# Forms
from app.forms import ContactForm, BlogPostForm, ProfileEditForm

# Routes
from app.routes import main, auth, blogpost, mc, admin, health, profile

# Utilities
from app.utils import (
    require_role,
    require_any_role,
    register_filters,
    validate_image_file
)
```

## 📝 License

This project is licensed under the terms specified in the LICENSE file.