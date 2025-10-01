# Deployment Guide

Flask Portfolio Site - Setup and Deployment Instructions

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Docker Development Setup](#docker-development-setup)
- [Production Deployment](#production-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Initialization](#database-initialization)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

---

## Prerequisites

### Required Software

**Local Development**:
- Python 3.11+
- PostgreSQL 15+
- pip (Python package manager)
- virtualenv or venv

**Docker Development**:
- Docker 20.10+
- Docker Compose 2.0+

**Production**:
- Docker & Docker Compose (recommended)
- OR Python 3.11+ with Gunicorn and PostgreSQL

**Optional**:
- Git (for version control)
- Portainer (for container orchestration UI)

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd flask-site
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_TYPE=postgresql
DB_USERNAME=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=flask_portfolio

# Flask Configuration
SECRET_KEY=your-secret-key-change-this-in-production
FLASK_ENV=development
REGISTRATION_ENABLED=True

# Minecraft RCON (optional)
RCON_PASS=your_rcon_password
MC_HOST=minecraft.server.com
MC_PORT=25575

# Email Configuration (for contact form)
MAIL_USER=your_gmail_account@gmail.com
MAIL_PW=your_gmail_app_password
```

**Security Notes**:
- Never commit `.env` to version control (add to `.gitignore`)
- Generate a strong SECRET_KEY: `python -c 'import secrets; print(secrets.token_hex(32))'`
- Use app-specific passwords for Gmail (not your account password)

### 5. Set Up PostgreSQL Database

**Option A: Local PostgreSQL**
```bash
# Create database
psql -U postgres
CREATE DATABASE flask_portfolio;
CREATE USER flask_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE flask_portfolio TO flask_user;
\q
```

**Option B: Docker PostgreSQL**
```bash
docker run -d \
  --name flask-postgres \
  -e POSTGRES_DB=flask_portfolio \
  -e POSTGRES_USER=flask_user \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  postgres:15-alpine
```

### 6. Initialize Database

```bash
# Create uploads directory
mkdir -p uploads/blog-posts

# Run migrations
flask db upgrade

# (Optional) Create admin user
python
>>> from app import create_app, db
>>> from app.models import User
>>> app = create_app()
>>> with app.app_context():
...     user = User(username='admin', email='admin@example.com')
...     user.set_password('secure_password')
...     db.session.add(user)
...     db.session.commit()
>>> exit()
```

### 7. Run Development Server

```bash
python run.py
```

Access the application at `http://localhost:8000`

---

## Docker Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd flask-site
```

### 2. Configure Environment

Create a `.env` file (see [Environment Configuration](#environment-configuration))

**Important**: Set `DB_HOST=postgres` (the service name in docker-compose.yml)

```env
DB_HOST=postgres
DB_PORT=5432
```

### 3. Build and Start Containers

```bash
# Build and start in detached mode
docker-compose up --build -d

# View logs
docker-compose logs -f flask-site
```

### 4. Run Migrations

```bash
# Apply database migrations
docker-compose exec flask-site flask db upgrade

# Verify migration status
docker-compose exec flask-site flask db current
```

### 5. Create Admin User (Optional)

```bash
docker-compose exec flask-site python
>>> from app import create_app, db
>>> from app.models import User
>>> app = create_app()
>>> with app.app_context():
...     user = User(username='admin', email='admin@example.com')
...     user.set_password('admin123')
...     db.session.add(user)
...     db.session.commit()
>>> exit()
```

### 6. Access Application

- **Application**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

### 7. Stop Containers

```bash
# Stop containers (preserves data)
docker-compose down

# Stop and remove volumes (deletes database!)
docker-compose down -v
```

---

## Production Deployment

### Option 1: Docker Compose (Recommended)

#### 1. Prepare Production Environment

```bash
# Clone repository on production server
git clone <repository-url>
cd flask-site

# Create production .env file
cp .env.example .env
nano .env  # Edit with production values
```

#### 2. Update docker-compose.yml for Production

**Recommended Changes**:

```yaml
services:
  flask-site:
    # Remove development volume mount
    volumes:
      - ./uploads:/app/uploads
      # REMOVE: - .:/app  (development only)

    # Optional: Expose postgres port only in development
    # Comment out postgres port mapping in production

  postgres:
    # ports:
    #   - "5433:5432"  # Comment out in production
```

#### 3. Deploy

```bash
# Build and start services
docker-compose up --build -d

# Run migrations
docker-compose exec flask-site flask db upgrade

# Create admin user
docker-compose exec flask-site python -c "
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
    user = User(username='admin', email='admin@example.com')
    user.set_password('secure_password')
    db.session.add(user)
    db.session.commit()
"

# Check health
curl http://localhost:8000/health
```

#### 4. Configure Reverse Proxy (Nginx)

**Example Nginx Configuration**:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads {
        proxy_pass http://localhost:8000/uploads;
    }
}
```

### Option 2: Manual Production Setup (Without Docker)

#### 1. Install Dependencies

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.11 python3-pip postgresql nginx

# Create app user
sudo useradd -m -s /bin/bash flask
```

#### 2. Set Up Application

```bash
# Clone as flask user
sudo su - flask
git clone <repository-url> /home/flask/app
cd /home/flask/app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with production values
```

#### 3. Configure Gunicorn Service

Create `/etc/systemd/system/flask-site.service`:

```ini
[Unit]
Description=Flask Portfolio Site
After=network.target

[Service]
Type=notify
User=flask
Group=flask
WorkingDirectory=/home/flask/app
Environment="PATH=/home/flask/app/venv/bin"
ExecStart=/home/flask/app/venv/bin/gunicorn --workers 6 --bind 127.0.0.1:8000 run:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

#### 4. Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable flask-site
sudo systemctl start flask-site
sudo systemctl status flask-site
```

### Option 3: Using grun.sh Script

**For simple production deployment on a server**:

```bash
# Make script executable
chmod +x grun.sh

# Run with nohup for background execution
nohup ./grun.sh > app.log 2>&1 &

# Or use screen/tmux
screen -S flask-site
./grun.sh
# Press Ctrl+A, then D to detach
```

**Note**: `grun.sh` uses 6 workers. Recommended worker count: `(2 x CPU cores) + 1`

---

## Environment Configuration

### Complete .env Template

```env
# ======================
# Database Configuration
# ======================
DATABASE_TYPE=postgresql
DB_USERNAME=flask_user
DB_PASSWORD=super_secure_password_change_me
DB_HOST=localhost          # Use 'postgres' for Docker Compose
DB_PORT=5432
DB_NAME=flask_portfolio

# ======================
# Flask Configuration
# ======================
SECRET_KEY=your-secret-key-generate-with-secrets-module
FLASK_ENV=production       # or 'development'
REGISTRATION_ENABLED=True  # Set to 'False' to disable new registrations

# ======================
# Minecraft RCON (Optional)
# ======================
RCON_PASS=minecraft_rcon_password
MC_HOST=minecraft.example.com
MC_PORT=25575

# ======================
# Email Configuration
# ======================
MAIL_USER=noreply@yourdomain.com
MAIL_PW=your_email_app_password

# ======================
# Optional Overrides
# ======================
# UPLOAD_FOLDER=/custom/path/to/uploads
```

### Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_TYPE` | Yes | - | Database type (postgresql) |
| `DB_USERNAME` | Yes | - | Database username |
| `DB_PASSWORD` | Yes | - | Database password |
| `DB_HOST` | Yes | - | Database host (localhost or postgres) |
| `DB_PORT` | Yes | - | Database port (5432) |
| `DB_NAME` | Yes | - | Database name |
| `SECRET_KEY` | Yes | `dev-key-please-change` | Flask secret key |
| `FLASK_ENV` | No | `production` | Environment (development/production) |
| `REGISTRATION_ENABLED` | No | `True` | Allow user registration |
| `RCON_PASS` | No | - | Minecraft RCON password |
| `MC_HOST` | No | - | Minecraft server host |
| `MC_PORT` | No | `25575` | Minecraft RCON port |
| `MAIL_USER` | No | - | SMTP email username |
| `MAIL_PW` | No | - | SMTP email password |
| `UPLOAD_FOLDER` | No | `uploads/blog-posts` | Upload directory |

---

## Database Initialization

### Create Initial Migration (First Time Only)

```bash
# Local
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Docker
docker-compose exec flask-site flask db init
docker-compose exec flask-site flask db migrate -m "Initial migration"
docker-compose exec flask-site flask db upgrade
```

### Apply Existing Migrations

```bash
# Local
flask db upgrade

# Docker
docker-compose exec flask-site flask db upgrade
```

### Create New Migration (After Model Changes)

```bash
# Local
flask db migrate -m "Add new field to model"
flask db upgrade

# Docker
docker-compose exec flask-site flask db migrate -m "Add new field to model"
docker-compose exec flask-site flask db upgrade
```

### Rollback Migration

```bash
# Rollback one migration
flask db downgrade

# Docker
docker-compose exec flask-site flask db downgrade
```

### Check Current Migration

```bash
# Local
flask db current

# Docker
docker-compose exec flask-site flask db current
```

---

## Troubleshooting

### Database Connection Issues

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Docker: Check container is healthy
docker-compose ps
docker-compose logs postgres

# Verify connection string in .env
# For Docker: DB_HOST=postgres (not localhost)

# Test database connection
docker-compose exec postgres psql -U flask_user -d flask_portfolio -c "SELECT 1"
```

### Migration Errors

**Problem**: `alembic.util.exc.CommandError: Target database is not up to date`

**Solution**:
```bash
# Check current migration version
flask db current

# Check migration history
flask db history

# Force stamp to specific version (use cautiously)
flask db stamp head
```

**Problem**: `ERROR [flask_migrate] Error: Can't locate revision identified by 'xyz'`

**Solution**:
```bash
# List all migration files
ls migrations/versions/

# Ensure all migration files are committed and present
git status migrations/
```

### Container Won't Start

**Problem**: Flask container exits immediately

**Solutions**:
```bash
# Check logs
docker-compose logs flask-site

# Common issues:
# 1. Database not ready - wait for postgres healthcheck
# 2. Missing environment variables - check .env file
# 3. Port already in use - change port mapping

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

### Health Check Failing

**Problem**: Health endpoint returns 503

**Solution**:
```bash
# Check health endpoint directly
curl http://localhost:8000/health

# Common causes:
# 1. Database connection failed
# 2. Application not fully started (wait 45s for start_period)

# Check database connectivity
docker-compose exec flask-site python -c "
from app import create_app
app = create_app()
with app.app_context():
    from app import db
    db.session.execute('SELECT 1')
    print('Database OK')
"
```

### File Upload Issues

**Problem**: Uploaded files not persisting

**Solutions**:
```bash
# Check uploads directory exists
ls -la uploads/blog-posts/

# Docker: Ensure volume is mounted
docker-compose exec flask-site ls -la /app/uploads/blog-posts/

# Check permissions
docker-compose exec flask-site ls -la /app/uploads/
# Should be owned by flask:flask (UID 1000)

# Fix permissions
docker-compose exec flask-site chown -R flask:flask /app/uploads/
```

### Permission Denied Errors

**Problem**: `PermissionError: [Errno 13] Permission denied`

**Solutions**:
```bash
# Local: Check file permissions
chmod -R 755 uploads/

# Docker: Container runs as flask user (UID 1000)
# Ensure host directory is writable
sudo chown -R 1000:1000 uploads/
```

---

## Maintenance

### Backup Database

```bash
# Docker PostgreSQL backup
docker-compose exec postgres pg_dump -U flask_user flask_portfolio > backup_$(date +%Y%m%d).sql

# Local PostgreSQL backup
pg_dump -U flask_user -h localhost flask_portfolio > backup_$(date +%Y%m%d).sql

# Automated daily backup (crontab)
0 2 * * * cd /path/to/flask-site && docker-compose exec -T postgres pg_dump -U flask_user flask_portfolio > backups/backup_$(date +\%Y\%m\%d).sql
```

### Restore Database

```bash
# Docker restore
cat backup_20251001.sql | docker-compose exec -T postgres psql -U flask_user flask_portfolio

# Local restore
psql -U flask_user -h localhost flask_portfolio < backup_20251001.sql
```

### Update Application

```bash
# Pull latest code
git pull origin main

# Docker deployment
docker-compose down
docker-compose up --build -d
docker-compose exec flask-site flask db upgrade

# Manual deployment
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart flask-site
```

### View Logs

```bash
# Docker logs
docker-compose logs -f flask-site
docker-compose logs -f postgres

# Filter logs by time
docker-compose logs --since 30m flask-site

# Systemd service logs (manual deployment)
sudo journalctl -u flask-site -f
```

### Monitor Resource Usage

```bash
# Docker stats
docker stats flask-site-dev flask-postgres-dev

# Check container health
docker-compose ps
```

### Clean Up

```bash
# Remove unused Docker images
docker image prune -a

# Remove unused volumes (WARNING: deletes data!)
docker volume prune

# Full cleanup (WARNING: deletes everything!)
docker-compose down -v
docker system prune -a --volumes
```

---

## Performance Tuning

### Gunicorn Workers

**Recommended formula**: `workers = (2 x CPU_cores) + 1`

```bash
# For 4-core machine
gunicorn --workers 9 --bind 0.0.0.0:8000 run:app

# Update in docker-compose.yml or grun.sh
```

### PostgreSQL Connection Pooling

Current settings (in `config.py`):
- `pool_timeout=10`: Wait up to 10s for connection
- `pool_recycle=300`: Recycle connections every 5 minutes
- `pool_pre_ping=True`: Test connections before use

### Resource Limits (Docker)

Adjust in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '4.0'
    reservations:
      memory: 512M
      cpus: '1.0'
```

---

## Security Checklist

- [ ] Generate strong `SECRET_KEY` (use `secrets.token_hex(32)`)
- [ ] Never commit `.env` file to version control
- [ ] Use HTTPS in production (configure reverse proxy)
- [ ] Set `FLASK_ENV=production` in production
- [ ] Use strong database passwords
- [ ] Disable `REGISTRATION_ENABLED` after creating admin users
- [ ] Keep dependencies updated (`pip list --outdated`)
- [ ] Configure firewall (allow only ports 80, 443)
- [ ] Enable PostgreSQL SSL connections in production
- [ ] Use app-specific passwords for email (not account password)
- [ ] Regularly backup database
- [ ] Monitor application logs for suspicious activity

---

## Quick Reference

### Common Commands

```bash
# Development server
python run.py

# Production server (local)
./grun.sh

# Docker build and start
docker-compose up --build -d

# View logs
docker-compose logs -f flask-site

# Run migrations
docker-compose exec flask-site flask db upgrade

# Access Flask shell
docker-compose exec flask-site flask shell

# Restart containers
docker-compose restart flask-site

# Stop all services
docker-compose down
```

### Health Check Endpoints

- `GET /health` - Application health check (includes DB status)

---

## Support

For issues, questions, or contributions, please refer to the project repository or contact the development team.
