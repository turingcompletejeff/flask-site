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
│       ├── css/            # Stylesheets
│       ├── js/             # JavaScript files
│       ├── img/            # Images
│       └── json/           # JSON data files
│
├── uploads/                # File upload directory
├── config.py               # Application configuration
├── run.py                  # Application entry point
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## ⚙️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/turingcompletejeff/flask-site.git
   cd flask-site
   ```

2. **Set up a Python virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```


## 🛡️ Environment Configuration

Never hardcode sensitive information! Create a `.env` file in the root directory:

```bash
DATABASE_URL=your_database_url_here
DB_USERNAME=your_db_username
DB_PASSWORD=your_db_password
RCON_PASS=your_rcon_password
MC_HOST=your_minecraft_server_host
MC_PORT=your_minecraft_server_port
SECRET_KEY=your_secret_key_here
REGISTRATION_ENABLED=true_or_false
```

Load environment variables in your application:

```python
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
```

## 🚀 Running the Application

**Development mode:**
```bash
python run.py
```
Then visit: http://localhost:8000

**Testing with docker:**
```bash
docker-compose down
docker-compose up --build -d flask-site
```
or 
```bash
docker-compose restart flask-site
```

## 🔧 Key Components

- **Authentication**: Modular user registration and login system
- **Blog Management**: Create, read, update, and delete blog posts
- **File Uploads**: Improved file handling with validation utilities
- **Minecraft Integration**: RCON-based server management
- **Responsive Design**: Mobile-friendly interface
- **Modular Architecture**: Improved code organization with directory-based separation of concerns

## 📝 Import Patterns

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
