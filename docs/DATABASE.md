# Database Schema Documentation

Flask Portfolio Site - Complete Database Reference

## Overview

**Database Type**: PostgreSQL
**ORM**: SQLAlchemy
**Migration Tool**: Flask-Migrate (Alembic)
**Connection Pooling**: Enabled with pre-ping health checks

---

## Table of Contents

- [Models](#models)
  - [User](#user-model)
  - [BlogPost](#blogpost-model)
  - [MinecraftCommand](#minecraftcommand-model)
- [Migration History](#migration-history)
- [Best Practices](#best-practices)
- [Common Operations](#common-operations)

---

## Models

### User Model

**Table Name**: `users`

**Description**: User authentication and account management

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `Integer` | Primary Key | Auto-incrementing user ID |
| `username` | `String(50)` | Unique, Not Null | Username for login |
| `email` | `String(120)` | Unique, Not Null | User email address |
| `password_hash` | `Text` | Not Null | Bcrypt hashed password |

**Indexes**:
- Primary key index on `id`
- Unique index on `username`
- Unique index on `email`

**Methods**:
- `set_password(password)`: Hash and store password using bcrypt
- `check_password(password)`: Verify password against stored hash
- `is_authenticated` (inherited): Flask-Login property
- `is_active` (inherited): Flask-Login property
- `get_id()` (inherited): Flask-Login method

**Relationships**: None

**Example**:
```python
from app.models import User

# Create new user
user = User(username='johndoe', email='john@example.com')
user.set_password('securepassword123')
db.session.add(user)
db.session.commit()

# Authenticate user
user = User.query.filter_by(username='johndoe').first()
if user and user.check_password('securepassword123'):
    login_user(user)
```

---

### BlogPost Model

**Table Name**: `blog_posts`

**Description**: Blog post content with draft/publish workflow

**Fields**:

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| `id` | `Integer` | Primary Key | Auto | Unique post identifier |
| `title` | `Text` | Not Null | - | Post title |
| `content` | `Text` | Not Null | - | Post content (HTML/Markdown) |
| `thumbnail` | `Text` | Nullable | NULL | Filename of thumbnail image (300x300) |
| `portrait` | `Text` | Nullable | NULL | Filename of portrait image |
| `themap` | `JSON` | Nullable | NULL | General-purpose JSON metadata |
| `date_posted` | `Date` | Not Null | `datetime.now` | Post creation date (local time) |
| `last_updated` | `DateTime` | Nullable | NULL | Last edit timestamp (UTC) |
| `is_draft` | `Boolean` | Not Null | `True` | Draft status (True=draft, False=published) |

**Indexes**:
- Primary key index on `id`

**JSON Schema** (`themap` field):
```json
{
  "portrait_display": {
    "display_mode": "auto" | "custom",
    "scale": 1.0,
    "translateX": 0,
    "translateY": 0
  }
}
```

**Methods**:
- `hasEdits()`: Returns `True` if `last_updated` is not None

**Relationships**: None

**Behavior Notes**:
- `date_posted`: Uses local time (no timezone awareness)
- `last_updated`: Uses UTC timezone (`datetime.now(timezone.utc)`)
- `last_updated`: Auto-updates on record modification via `onupdate` callback
- `is_draft`: Defaults to `True` (new posts are drafts by default)
- Thumbnails auto-generated at 300x300 if not provided
- Image filenames stored as relative paths (e.g., `portrait_image.jpg`)

**Example**:
```python
from app.models import BlogPost

# Create new draft post
post = BlogPost(
    title='My First Post',
    content='<p>This is the content...</p>',
    portrait='portrait_123.jpg',
    thumbnail='thumb_portrait_123.jpg',
    is_draft=True
)
db.session.add(post)
db.session.commit()

# Publish draft
post.is_draft = False
db.session.commit()

# Query published posts only
published = BlogPost.query.filter_by(is_draft=False).all()
```

---

### MinecraftCommand Model

**Table Name**: `minecraft_commands`

**Description**: Stored RCON commands for Minecraft server management

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `command_id` | `Integer` | Primary Key | Auto-incrementing command ID |
| `command_name` | `String(20)` | Nullable | Display name for command |
| `options` | `ARRAY(String(40))` | - | PostgreSQL array of command strings |

**Indexes**:
- Primary key index on `command_id`

**Methods**:
- `to_dict()`: Serialize to JSON-compatible dictionary

**PostgreSQL-Specific**:
- Uses native PostgreSQL `ARRAY` type
- Not portable to other databases without modification

**Example**:
```python
from app.models import MinecraftCommand

# Create command preset
cmd = MinecraftCommand(
    command_name='daylight',
    options=['time set day', 'weather clear']
)
db.session.add(cmd)
db.session.commit()

# Retrieve and serialize
commands = MinecraftCommand.query.all()
json_data = [cmd.to_dict() for cmd in commands]
# Returns: [{'command_id': 1, 'command_name': 'daylight', 'options': ['time set day', 'weather clear']}]
```

---

## Migration History

### Migration 1: `1350aca454f1` - Initial Migration
**Date**: 2025-09-30 22:22:25
**Revises**: None (initial)

**Changes**:
- Removed table-level comment from `blog_posts`
- Removed column comment from `thumbnail` field
- Changed `last_updated` type from `TIMESTAMP(timezone=True)` to `DateTime`

**Purpose**: Clean up schema metadata and normalize timestamp handling

---

### Migration 2: `ba76cbd4fd71` - Add is_draft Field
**Date**: 2025-10-01 17:44:00
**Revises**: `1350aca454f1`

**Changes**:
- Added `is_draft` Boolean column to `blog_posts`
- Set `nullable=False` with `server_default='false'`
- Existing posts marked as published (`False`) by default

**Purpose**: Implement draft/publish workflow (TC-4)

**Best Practice Demonstrated**:
- Used `server_default` to allow adding non-nullable column to existing table
- Safely backfills existing data without breaking constraints

---

## Best Practices

### Migration Best Practices

1. **Adding Non-Nullable Columns**:
   ```python
   # GOOD: Use server_default for existing data
   batch_op.add_column(sa.Column('is_draft', sa.Boolean(),
                                  nullable=False,
                                  server_default='false'))

   # BAD: Will fail if table has existing rows
   batch_op.add_column(sa.Column('is_draft', sa.Boolean(),
                                  nullable=False))
   ```

2. **Testing Migrations**:
   ```bash
   # Apply migration
   docker-compose exec flask-site flask db upgrade

   # Verify current version
   docker-compose exec flask-site flask db current

   # Test rollback
   docker-compose exec flask-site flask db downgrade

   # Re-apply
   docker-compose exec flask-site flask db upgrade
   ```

3. **Migration Workflow**:
   ```bash
   # 1. Modify models in app/models.py
   # 2. Generate migration
   docker-compose exec flask-site flask db migrate -m "Add new field"

   # 3. Review generated migration file in migrations/versions/
   # 4. Test migration
   docker-compose exec flask-site flask db upgrade

   # 5. Commit both model changes AND migration file
   git add app/models.py migrations/versions/*.py
   git commit -m "Add new field to model"
   ```

4. **JSON Field Updates**:
   ```python
   from sqlalchemy.orm.attributes import flag_modified

   # Modify JSON field
   post.themap['portrait_display'] = {"display_mode": "custom"}

   # IMPORTANT: Tell SQLAlchemy the JSON changed
   flag_modified(post, 'themap')

   db.session.commit()
   ```

5. **Connection Pooling Configuration**:
   - `pool_pre_ping=True`: Test connections before use (handles stale connections)
   - `pool_recycle=300`: Recycle connections after 5 minutes (prevents timeouts)
   - `pool_timeout=10`: Wait up to 10 seconds for available connection

---

## Common Operations

### Querying

```python
# Get all published posts
published = BlogPost.query.filter_by(is_draft=False).all()

# Get posts ordered by date
recent = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()

# Get single post or 404
post = BlogPost.query.get_or_404(post_id)

# Complex filter
from datetime import date
today_posts = BlogPost.query.filter(
    BlogPost.date_posted == date.today(),
    BlogPost.is_draft == False
).all()
```

### Creating Records

```python
# Create and save in one transaction
post = BlogPost(title='Test', content='Content', is_draft=True)
db.session.add(post)
db.session.commit()

# Bulk create
posts = [
    BlogPost(title=f'Post {i}', content=f'Content {i}')
    for i in range(10)
]
db.session.add_all(posts)
db.session.commit()
```

### Updating Records

```python
# Update single field
post = BlogPost.query.get(1)
post.title = 'New Title'
db.session.commit()  # last_updated auto-updates

# Update multiple fields
post.title = 'Updated'
post.content = 'New content'
post.is_draft = False
db.session.commit()
```

### Deleting Records

```python
# Delete single record
post = BlogPost.query.get(1)
db.session.delete(post)
db.session.commit()

# Delete with query
BlogPost.query.filter_by(is_draft=True).delete()
db.session.commit()
```

### Transaction Rollback

```python
try:
    post = BlogPost(title='Test', content='Content')
    db.session.add(post)
    db.session.commit()
except Exception as e:
    db.session.rollback()
    print(f"Error: {e}")
```

---

## Database Connection

**Connection String Format**:
```
postgresql://username:password@host:port/database?connect_timeout=10
```

**Environment Variables Required**:
- `DATABASE_TYPE`: `postgresql`
- `DB_USERNAME`: Database user
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host
- `DB_PORT`: Database port (usually `5432`)
- `DB_NAME`: Database name

**Example `.env`**:
```
DATABASE_TYPE=postgresql
DB_USERNAME=flask_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=flask_portfolio
```

---

## Indexes and Performance

**Current Indexes**:
- All primary keys have automatic indexes
- `users.username` has unique index
- `users.email` has unique index

**Potential Optimizations** (not currently implemented):
- Index on `blog_posts.is_draft` (if filtering published posts frequently)
- Index on `blog_posts.date_posted` (for ordering by date)
- Composite index on `(is_draft, date_posted)` (for common query pattern)

**Add Index Example**:
```python
# In migration file
def upgrade():
    with op.batch_alter_table('blog_posts', schema=None) as batch_op:
        batch_op.create_index('idx_is_draft', ['is_draft'])
```

---

## Data Integrity

**Constraints**:
- Foreign keys: None currently defined
- Unique constraints: `users.username`, `users.email`
- Not null constraints: See individual model field tables

**Password Security**:
- Passwords hashed using Werkzeug's `generate_password_hash()`
- Uses bcrypt algorithm by default
- Never store plaintext passwords
- Password hashes stored in `Text` field (accommodates hash length)

**File References**:
- `BlogPost.portrait` and `BlogPost.thumbnail` store filenames only
- Files stored on disk in `uploads/blog-posts/` directory
- No foreign key to file storage (manual cleanup required on delete)

---

## Backup and Restore

**Backup Database** (PostgreSQL):
```bash
# From host machine
pg_dump -U username -h localhost -p 5432 flask_portfolio > backup.sql

# From Docker container
docker-compose exec db pg_dump -U flask_user flask_portfolio > backup.sql
```

**Restore Database**:
```bash
# From host machine
psql -U username -h localhost -p 5432 flask_portfolio < backup.sql

# From Docker container
docker-compose exec -T db psql -U flask_user flask_portfolio < backup.sql
```

---

## Schema Visualization

```
┌─────────────────────┐
│      users          │
├─────────────────────┤
│ id (PK)             │
│ username (UNIQUE)   │
│ email (UNIQUE)      │
│ password_hash       │
└─────────────────────┘

┌──────────────────────────┐
│     blog_posts           │
├──────────────────────────┤
│ id (PK)                  │
│ title                    │
│ content                  │
│ thumbnail                │
│ portrait                 │
│ themap (JSON)            │
│ date_posted              │
│ last_updated             │
│ is_draft                 │
└──────────────────────────┘

┌──────────────────────────┐
│  minecraft_commands      │
├──────────────────────────┤
│ command_id (PK)          │
│ command_name             │
│ options (ARRAY)          │
└──────────────────────────┘
```

---

## Notes

- No foreign key relationships defined between models
- All models use auto-incrementing integer primary keys
- PostgreSQL-specific features used: `JSON` type, `ARRAY` type
- Timezone handling inconsistent: `date_posted` (no TZ), `last_updated` (UTC)
- File cleanup not automated (orphaned files possible after post deletion)
- Consider adding cascade delete for uploaded files
- Consider adding created_at/updated_at timestamps to User model
