# flask-site
portfolio site to host a blog and my projects

# 📌 Features

+ hosts a blog on the home page
   + CRUD blog posts, text, image, HTML encoding
+ minecraft page:
   + connect to a minecraft server with RCON
   + send commands
   + list players connected

# 📂 Project Structure

flask-site/
│
├── app/                # Main application package
│   ├── __init__.py     # Initializes the Flask application and sets up configurations
│   ├── routes.py       # Defines the routes (views) for the app
│   ├── models.py       # Database models (if using an ORM like SQLAlchemy)
│   ├!! forms.py        # Web forms 
│   ├── templates/      # HTML templates (for Jinja2)
│   │   ├~~ layout.html # Base layout template
│   │   ├── index.html  # Home page
│   └── static/         # Static files (CSS, JavaScript, images)
│       ├~~ css/
│       ├~~ js/
│       └── img/
│
├!! migrations/         # Database migration files (if using Flask-Migrate)
│
├!! tests/              # Test cases for the application
│   ├!! __init__.py
│   ├!! test_basic.py   # Example test case
│
├── .env                # Environment variables (for secret keys, config settings, etc.)
├── config.py           # Application configurations
├── run.py              # Run the Flask application
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation

------------------------------------------------------------
⚙️ Installation
------------------------------------------------------------
1. Clone the repository:
   git clone https://github.com/turingcompletejeff/flask-site.git
   cd flask-site

2. Install dependencies:

   pip install -r requirements.txt

------------------------------------------------------------
🛡️ Secure Password Storage
------------------------------------------------------------
Never hardcode your database connection info or passwords!!  
Instead, create a `.env` file in the root directory:

-------------
DATABASE_URL=
DB_USERNAME=
DB_PASSWORD=
RCON_PASS=
MC_HOST=
MC_PORT=
SECRET_KEY=
REGISTRATION_ENABLED=
-------------

In app.py (or elsewhere), load it with:

from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

------------------------------------------------------------
🚀 Running the App
------------------------------------------------------------
Development mode:
   python run.py
Then visit: http://localhost
