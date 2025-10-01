# API Documentation

Flask Portfolio Site - Complete API Reference

## Table of Contents

- [Main Blueprint (`main_bp`)](#main-blueprint-main_bp)
- [Auth Blueprint (`auth`)](#auth-blueprint-auth)
- [Blog Post Blueprint (`blogpost_bp`)](#blog-post-blueprint-blogpost_bp)
- [Minecraft Blueprint (`mc_bp`)](#minecraft-blueprint-mc_bp)
- [Health Blueprint (`health_bp`)](#health-blueprint-health_bp)

---

## Main Blueprint (`main_bp`)

Routes for public-facing pages and core functionality.

### GET `/`

**Description**: Home page displaying blog posts

**Authentication**: Not required

**Query Parameters**:
- `flash` (optional): Flash message to display
- `category` (optional): Flash message category (`info`, `success`, `warning`, `danger`). Default: `info`

**Response**: Rendered HTML template (`index.html`)

**Behavior**:
- Authenticated users see all blog posts (drafts + published)
- Public users only see published posts (where `is_draft=False`)
- Posts ordered by `date_posted` descending, then `id` descending

**Example**:
```
GET /?flash=Welcome&category=success
```

---

### GET `/about`

**Description**: About page

**Authentication**: Not required

**Response**: Rendered HTML template (`about.html`)

---

### GET/POST `/contact`

**Description**: Contact form submission endpoint

**Authentication**: Not required

**Methods**: `GET`, `POST`

**Request Body** (POST, form-encoded):
- `name` (required): Contact name
- `email` (required): Contact email address
- `phone` (optional): Contact phone number
- `reason` (required): Reason for contact
- `message` (required): Contact message

**Response**:
- **Success (HTML)**: Redirect to `/` with success flash message
- **Success (AJAX/JSON)**: `200 OK`
  ```json
  {
    "success": true,
    "message": "message sent from user@example.com",
    "redirect": "/"
  }
  ```
- **Error (HTML)**: Re-render form with error flash message
- **Error (AJAX/JSON)**: `500 Internal Server Error`
  ```json
  {
    "success": false,
    "error": "Failed to send message. Please try again."
  }
  ```

**Notes**:
- Supports both traditional form submission and AJAX requests
- AJAX detection via `X-Requested-With: XMLHttpRequest` header or `Accept: application/json`
- Sends email to configured admin address via SMTP

---

### GET `/uploads/blog-posts/<filename>`

**Description**: Serve uploaded blog post images

**Authentication**: Not required

**Path Parameters**:
- `filename`: Name of the file to serve

**Response**: File from `BLOG_POST_UPLOAD_FOLDER` directory

**Example**:
```
GET /uploads/blog-posts/portrait_image.jpg
```

---

## Auth Blueprint (`auth`)

Routes for user authentication and registration.

### GET/POST `/login`

**Description**: User login page

**Authentication**: Not required

**Methods**: `GET`, `POST`

**Request Body** (POST, form-encoded):
- `username` (required): User's username
- `password` (required): User's password

**Response**:
- **Success**: Redirect to `/` with success flash message
- **Failure**: Re-render login page with error flash message

**Example POST**:
```
POST /login
Content-Type: application/x-www-form-urlencoded

username=admin&password=securepass123
```

---

### GET/POST `/register`

**Description**: User registration page

**Authentication**: Not required

**Methods**: `GET`, `POST`

**Configuration**: Only accessible if `REGISTRATION_ENABLED=True` in app config

**Request Body** (POST, form-encoded):
- `username` (required): Desired username (must be unique)
- `password` (required): Desired password
- `email` (required): Email address

**Response**:
- **Success**: Redirect to `/login` with success flash message
- **Username taken**: Re-render with error flash message
- **Registration disabled**: Redirect to `/` with warning flash message

**Example POST**:
```
POST /register
Content-Type: application/x-www-form-urlencoded

username=newuser&password=pass123&email=user@example.com
```

---

### GET `/logout`

**Description**: Log out current user

**Authentication**: Required (`@login_required`)

**Response**: Redirect to `/` with info flash message

---

## Blog Post Blueprint (`blogpost_bp`)

Routes for blog post management (CRUD operations).

### GET `/post/<int:post_id>`

**Description**: View a single blog post

**Authentication**: Not required (but affects visibility)

**Path Parameters**:
- `post_id`: Integer ID of the blog post

**Response**:
- **Success**: Rendered HTML template (`view_post.html`)
- **Draft post + unauthenticated user**: Redirect to `/` with error flash message
- **Post not found**: `404 Not Found`

**Behavior**:
- Draft posts (`is_draft=True`) only visible to authenticated users
- Public users attempting to view draft posts are redirected

---

### GET/POST `/post/new`

**Description**: Create a new blog post

**Authentication**: Required (`@login_required`)

**Methods**: `GET`, `POST`

**Request Body** (POST, multipart/form-data):
- `title` (required): Post title
- `content` (required): Post content (supports HTML/Markdown)
- `portrait` (optional): Portrait image file upload
- `thumbnail` (optional): Custom thumbnail image file upload
- `portrait_resize_params` (optional): JSON string with portrait display settings
- `publish` (button): If submitted, post is published (`is_draft=False`)
- `save_draft` (button): If submitted, post saved as draft (`is_draft=True`)

**Response**:
- **Success**: Redirect to `/` with success flash message
  - "Draft saved!" if saved as draft
  - "Post published!" if published
- **Validation error**: Re-render form with validation errors

**Behavior**:
- Default draft status: `True` (draft)
- Portrait images saved to `BLOG_POST_UPLOAD_FOLDER`
- Thumbnail handling:
  1. If custom thumbnail uploaded: resize to 300x300, saved with `custom_thumb_` prefix
  2. If only portrait uploaded: auto-generate 300x300 thumbnail with `thumb_` prefix
- Portrait resize parameters stored in `themap` JSON field under `portrait_display` key

**Example portrait_resize_params**:
```json
{
  "display_mode": "custom",
  "scale": 1.2,
  "translateX": 0,
  "translateY": -50
}
```

---

### POST `/post/delete`

**Description**: Delete a blog post

**Authentication**: Required (`@login_required`)

**Request Body** (form-encoded):
- `id` (required): ID of the post to delete

**Response**: Redirect to `/` with success flash message

---

### GET/POST `/post/<int:post_id>/edit`

**Description**: Edit an existing blog post

**Authentication**: Required (`@login_required`)

**Methods**: `GET`, `POST`

**Path Parameters**:
- `post_id`: Integer ID of the blog post

**Request Body** (POST, form-encoded):
- `title` (required): Updated post title
- `content` (required): Updated post content
- `portrait_resize_params` (optional): JSON string with portrait display settings
- `publish` (button): If submitted, post is published (`is_draft=False`)
- `save_draft` (button): If submitted, post saved as draft (`is_draft=True`)

**Response**:
- **Success**: Redirect to `/post/<post_id>` with success flash message
  - "Draft saved!" if saved as draft
  - "Post published!" if published
  - "Post updated!" if neither button specified
- **Validation error**: Re-render form with validation errors
- **Post not found**: `404 Not Found`

**Behavior**:
- Pre-populates form with existing post data on GET
- Updates `last_updated` timestamp automatically
- Dual submit button support: "Save as Draft" and "Publish"
- Portrait resize parameters update `themap` JSON field
- Uses `flag_modified()` to ensure SQLAlchemy detects JSON field changes

---

## Minecraft Blueprint (`mc_bp`)

Routes for Minecraft server RCON integration.

**Global Authentication**: All routes require authentication (enforced via `@mc_bp.before_request`)

### GET `/mc`

**Description**: Minecraft control panel page

**Authentication**: Required (blueprint-level)

**Response**: Rendered HTML template (`mc.html`)

---

### GET `/mc/init`

**Description**: Initialize RCON connection

**Authentication**: Required (blueprint-level)

**Response**:
- **Success**: Help command output from Minecraft server
- **Failure**: String `"FAIL"`

**Behavior**:
- Establishes RCON connection to Minecraft server
- Tests connection with `help` command
- Uses config values: `RCON_HOST`, `RCON_PORT`, `RCON_PASSWORD`

---

### GET `/mc/stop`

**Description**: Stop RCON connection

**Authentication**: Required (blueprint-level)

**Response**: String `"OK"`

**Behavior**:
- Terminates active RCON connection
- Resets global `rcon` variable to `None`

---

### POST `/mc/command`

**Description**: Execute RCON command on Minecraft server

**Authentication**: Required (blueprint-level)

**CSRF Protection**: Exempt (allows external tools to send commands)

**Request Body** (form-encoded):
- `command` (required): Minecraft command to execute (without leading `/`)

**Response**:
- **Success**: Command output from Minecraft server (plain text)
- **Failure**: String `"FAIL"`

**Example**:
```
POST /mc/command
Content-Type: application/x-www-form-urlencoded

command=list
```

**Response Example**:
```
There are 3 of a max of 20 players online: Player1, Player2, Player3
```

---

### GET `/mc/query`

**Description**: Query Minecraft server status via Query protocol

**Authentication**: Required (blueprint-level)

**Response**:
- **Success**: `200 OK` with full server stats (JSON)
- **Connection error**: `500 Internal Server Error`
  ```json
  {
    "error": "Connection closed",
    "message": "error details..."
  }
  ```

**Behavior**:
- Uses Minecraft Query protocol (separate from RCON)
- Returns player list, server version, plugins, etc.

---

### GET `/mc/list`

**Description**: List all saved Minecraft commands

**Authentication**: Required (blueprint-level)

**Response**: `200 OK` with JSON array of command objects

**Example Response**:
```json
[
  {
    "command_id": 1,
    "command_name": "daylight",
    "options": ["time set day", "weather clear"]
  },
  {
    "command_id": 2,
    "command_name": "teleport",
    "options": ["tp @p 0 100 0"]
  }
]
```

---

## Health Blueprint (`health_bp`)

Routes for health checks and monitoring.

### GET `/health`

**Description**: Health check endpoint for monitoring and container orchestration

**Authentication**: Not required

**Response**:
- **All systems healthy**: `200 OK`
- **Any system unhealthy**: `503 Service Unavailable`

**Response Format** (JSON):
```json
{
  "status": "healthy",
  "timestamp": "2025-10-01T16:50:00.000000+00:00",
  "version": "1.0.0",
  "checks": {
    "app": {
      "status": "up",
      "message": "Application running"
    },
    "database": {
      "status": "up",
      "message": "Database connected",
      "response_time_ms": 12.45,
      "cached": false
    }
  }
}
```

**Behavior**:
- Database check cached for 30 seconds (TTL)
- Cached responses include `"cached": true` in database check
- Application check always returns `"up"` if endpoint is reachable
- Suitable for Docker health checks, load balancer health probes, etc.

---

## Common Response Codes

- `200 OK`: Successful request
- `302 Found`: Redirect (after POST operations, auth redirects)
- `404 Not Found`: Resource not found (blog post, uploaded file)
- `500 Internal Server Error`: Server error (email failure, database error)
- `503 Service Unavailable`: Health check failed

---

## Authentication

**Method**: Session-based authentication via Flask-Login

**Login Flow**:
1. POST credentials to `/login`
2. Server sets session cookie
3. Subsequent requests include session cookie
4. Protected routes check `current_user.is_authenticated`

**Protected Routes** (require `@login_required`):
- `/logout`
- `/post/new`
- `/post/delete`
- `/post/<post_id>/edit`
- All `/mc/*` routes (blueprint-level protection)

---

## CSRF Protection

**Global Protection**: Enabled for all POST/PUT/DELETE requests

**Exemptions**:
- `/mc/command` (allows external RCON tools)
- Read-only endpoints (GET requests)

**Usage**: Include CSRF token in forms:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
```

---

## File Uploads

**Upload Endpoint**: POST to `/post/new` or `/post/<post_id>/edit`

**Accepted Fields**:
- `portrait`: Main image for blog post
- `thumbnail`: Custom thumbnail (optional)

**Storage Location**: `BLOG_POST_UPLOAD_FOLDER` (default: `uploads/blog-posts/`)

**Serving Uploads**: GET `/uploads/blog-posts/<filename>`

**Image Processing**:
- All images sanitized with `secure_filename()`
- Thumbnails resized to 300x300 using PIL/Pillow
- Auto-generated thumbnails prefixed with `thumb_`
- Custom thumbnails prefixed with `custom_thumb_`

**Security**:
- Filenames sanitized to prevent directory traversal
- No file type restrictions documented (consider adding validation)

---

## Error Handling

**Flash Messages**: User-facing errors communicated via Flask flash messages

**Flash Categories**:
- `success`: Successful operations (green)
- `info`: Informational messages (blue)
- `warning`: Warnings (yellow)
- `danger`/`error`: Errors (red)

**AJAX Error Responses**: Return JSON with `success: false` and `error` message

---

## Notes

- All timestamps stored in UTC (`datetime.now(timezone.utc)`)
- Blog post `date_posted` uses `datetime.now` (no timezone, local time)
- Draft posts filtered at query level (not template level)
- Minecraft RCON connection is global and persistent (reused across requests)
- Email configuration required for contact form functionality
- Registration can be disabled via `REGISTRATION_ENABLED` config flag
