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
│   ├── routes.py           # Main application routes
│   ├── routes_auth.py      # Authentication routes (login, register)
│   ├── routes_blogpost.py  # Blog post CRUD routes
│   ├── routes_mc.py        # Minecraft server integration routes
│   ├── models.py           # Database models
│   ├── forms.py            # WTForms form definitions
│   ├── filters.py          # Custom Jinja2 template filters
│   │
│   ├── templates/          # HTML templates (Jinja2)
│   │   ├── layout.html     # Base layout template
│   │   ├── index.html      # Home page template
│   │   ├── about.html      # About page template
│   │   ├── about_text.html # About page content
│   │   ├── contact.html    # Contact page template
│   │   ├── login.html      # Login form template
│   │   ├── register.html   # Registration form template
│   │   ├── view_post.html  # Blog post view template
│   │   ├── edit_post.html  # Blog post edit template
│   │   ├── mc.html         # Minecraft server page template
│   │   └── macros/         # Reusable template macros
│   │
│   └── static/             # Static files (CSS, JavaScript, images)
│       ├── css/            # Stylesheets
│       ├── js/             # JavaScript files
│       ├── img/            # Images
│       └── json/           # JSON data files
│
├── uploads/                # File upload directory
├── config.py              # Application configuration
├── run.py                 # Application entry point
├── requirements.txt       # Python dependencies
├── grun.sh               # Deployment/run script
├── .gitignore            # Git ignore rules
├── LICENSE               # License file
└── README.md             # Project documentation
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
Then visit: http://localhost:5000

**Production deployment (recommended):**

For server deployment, I typically use `screen` to create a detached session:

```bash
screen -S flask-site
./grun.sh
```

The `grun.sh` script runs the application using Gunicorn with optimized settings for production. You can detach from the screen session with `Ctrl+A, D` and reattach later with `screen -r flask-site`.

For more information about Gunicorn configuration and deployment options, see the [Gunicorn documentation](https://docs.gunicorn.org/en/stable/settings.html).

## 🔧 Key Components

- **Authentication**: User registration and login system
- **Blog Management**: Create, read, update, and delete blog posts
- **File Uploads**: Support for image and file uploads
- **Minecraft Integration**: RCON-based server management
- **Responsive Design**: Mobile-friendly interface

## 📝 License

This project is licensed under the terms specified in the LICENSE file.
