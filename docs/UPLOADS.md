# File Upload System Documentation

Flask Portfolio Site - Image Upload and Processing Guide

## Table of Contents

- [Overview](#overview)
- [Upload Flow](#upload-flow)
- [Directory Structure](#directory-structure)
- [File Validation](#file-validation)
- [Image Processing](#image-processing)
- [Security Considerations](#security-considerations)
- [Configuration](#configuration)
- [Common Operations](#common-operations)
- [Troubleshooting](#troubleshooting)

---

## Overview

The file upload system handles blog post images with automatic thumbnail generation and storage. It supports portrait images for posts and optional custom thumbnails.

**Key Features**:
- Secure filename sanitization
- Automatic thumbnail generation (300x300)
- Custom thumbnail upload support
- PIL/Pillow-based image processing
- Configurable upload directory
- File size limits (15MB default)

**Supported Formats**:
- JPG/JPEG
- PNG

---

## Upload Flow

### 1. Portrait-Only Upload

```
User uploads portrait image
    ↓
Filename sanitized (secure_filename)
    ↓
Portrait saved to uploads/blog-posts/
    ↓
Thumbnail auto-generated (300x300)
    ↓
Thumbnail saved as thumb_<filename>
    ↓
Both filenames stored in BlogPost record
```

### 2. Portrait + Custom Thumbnail Upload

```
User uploads portrait + custom thumbnail
    ↓
Both filenames sanitized
    ↓
Portrait saved to uploads/blog-posts/
    ↓
Custom thumbnail saved and resized to 300x300
    ↓
Custom thumbnail saved as custom_thumb_<filename>
    ↓
Both filenames stored in BlogPost record
```

### 3. No Upload (Text-Only Post)

```
User submits post without images
    ↓
portrait = None
thumbnail = None
    ↓
Post saved with no image references
```

---

## Directory Structure

```
flask-site/
├── uploads/
│   └── blog-posts/
│       ├── portrait_image1.jpg          # Original portrait
│       ├── thumb_portrait_image1.jpg     # Auto-generated thumbnail
│       ├── portrait_image2.png          # Another portrait
│       ├── custom_thumb_thumbnail2.jpg  # Custom thumbnail
│       └── ...
├── app/
│   ├── routes_blogpost.py              # Upload logic
│   └── forms.py                        # File field validation
└── config.py                           # Upload folder config
```

**Docker Volume Mapping**:
```yaml
volumes:
  - ./uploads:/app/uploads  # Persist uploads outside container
```

---

## File Validation

### Form-Level Validation

**Location**: `app/forms.py`

```python
class BlogPostForm(FlaskForm):
    portrait = FileField("Portrait",
                        validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    thumbnail = FileField("Custom Thumbnail (Optional)",
                         validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
```

**Allowed Extensions**:
- `.jpg`
- `.jpeg`
- `.png`

**Validation Behavior**:
- File extension checked before upload
- Case-insensitive extension matching
- Upload rejected if extension not in allowed list
- Flash error message shown to user

### Application-Level Limits

**Location**: `config.py`

```python
MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15MB limit
```

**Behavior**:
- Flask enforces size limit globally
- Requests exceeding limit return `413 Request Entity Too Large`
- Limit applies to entire request body (not per file)

---

## Image Processing

### Thumbnail Generation

**Library**: PIL/Pillow (`from PIL import Image`)

**Process**:

1. **Auto-Generated Thumbnail** (from portrait):
   ```python
   img = Image.open(file_path)
   img.thumbnail((300, 300))  # Maintains aspect ratio
   img.save(thumb_path)
   ```

2. **Custom Thumbnail** (user-uploaded):
   ```python
   thumbnail_file.save(thumb_path)
   img = Image.open(thumb_path)
   img.thumbnail((300, 300))  # Resize to max 300x300
   img.save(thumb_path)
   ```

**Thumbnail Behavior**:
- Target size: 300x300 pixels
- Aspect ratio preserved (not cropped)
- Fits image within 300x300 bounding box
- Example: 600x400 → 300x200, 400x600 → 200x300

### Portrait Display Parameters

**Stored in**: `BlogPost.themap` JSON field

**Schema**:
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

**Modes**:
- `auto`: Default display (no transformations)
- `custom`: User-defined scale and translation for cropping/positioning

**Usage** (from `routes_blogpost.py`):
```python
resize_params = json.loads(request.form.get('portrait_resize_params'))
themap_data['portrait_display'] = resize_params
```

---

## Security Considerations

### Filename Sanitization

**Function**: `werkzeug.utils.secure_filename()`

**Purpose**: Prevent directory traversal attacks

**Example**:
```python
from werkzeug.utils import secure_filename

# Dangerous filenames
secure_filename("../../../etc/passwd")  # Returns: "etc_passwd"
secure_filename("my file (1).jpg")      # Returns: "my_file_1.jpg"
secure_filename("über_image.png")       # Returns: "uber_image.png"
```

**Applied In**:
```python
filename = secure_filename(portrait_file.filename)
thumbnailname = f"custom_thumb_{secure_filename(thumbnail_file.filename)}"
```

### File Extension Validation

**Current Implementation**: Flask-WTF `FileAllowed` validator

**Limitations**:
- Only checks file extension (not content)
- Does not validate file headers/magic bytes
- Trusts user-provided MIME type

**Recommendation** (not currently implemented):
```python
import imghdr

def validate_image(file_path):
    """Validate image by checking file headers"""
    img_type = imghdr.what(file_path)
    return img_type in ['jpeg', 'png']
```

### Storage Location

**Current**: `uploads/blog-posts/` within application directory

**Security Notes**:
- Files served via Flask route `/uploads/blog-posts/<filename>`
- No directory listing enabled
- Files accessible to anyone with filename
- No authentication required to view uploaded images

**Potential Improvements**:
- Move uploads outside web root
- Implement access control for draft post images
- Add signed URLs for temporary access

### File Size Limits

**Global Limit**: 15MB (`MAX_CONTENT_LENGTH`)

**Rationale**:
- Prevents denial-of-service via large uploads
- Protects disk space
- Reasonable for high-quality images

**Per-File Limits** (not implemented):
```python
# Could add field-level validators
FileField("Portrait", validators=[
    FileAllowed(['jpg', 'png', 'jpeg']),
    FileSize(max_size=5 * 1024 * 1024)  # 5MB per file
])
```

---

## Configuration

### Environment Variables

**UPLOAD_FOLDER** (optional):
```env
UPLOAD_FOLDER=/custom/path/to/uploads
```

**Default**: `uploads/blog-posts/` (relative to application root)

### Application Config

**Location**: `config.py`

```python
BLOG_POST_UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads/blog-posts')
MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15MB
```

**Override Example**:
```python
import os

BLOG_POST_UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER',
                                         os.path.join(os.getcwd(), 'uploads/blog-posts'))
```

### Docker Configuration

**Volume Mount** (docker-compose.yml):
```yaml
volumes:
  - ./uploads:/app/uploads
```

**Permissions** (Dockerfile):
```dockerfile
RUN mkdir -p uploads/blog-posts && \
    chown -R flask:flask uploads/
```

**UID/GID**: Container runs as `flask` user (UID 1000, GID 1000)

---

## Common Operations

### Upload Image (New Post)

**Endpoint**: `POST /post/new`

**Form Data**:
```html
<form method="POST" enctype="multipart/form-data">
  <input type="file" name="portrait">
  <input type="file" name="thumbnail">
  <input type="hidden" name="portrait_resize_params" value='{"display_mode":"auto"}'>
  <button type="submit" name="publish">Publish</button>
</form>
```

**Backend Processing**:
1. Validate file extensions
2. Sanitize filenames
3. Save portrait to disk
4. Generate or process thumbnail
5. Store filenames in database
6. Redirect to home page

### Serve Uploaded Image

**Endpoint**: `GET /uploads/blog-posts/<filename>`

**Implementation** (routes.py):
```python
@main_bp.route('/uploads/blog-posts/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['BLOG_POST_UPLOAD_FOLDER'], filename)
```

**Usage in Templates**:
```html
<img src="{{ url_for('main_bp.uploaded_file', filename=post.portrait) }}" alt="Portrait">
<img src="{{ url_for('main_bp.uploaded_file', filename=post.thumbnail) }}" alt="Thumbnail">
```

### Delete Post (Orphaned Files)

**Current Behavior**: Files remain on disk after post deletion

**Code** (routes_blogpost.py):
```python
@blogpost_bp.route('/post/delete', methods=['POST'])
@login_required
def delete_post():
    post_id = request.form.get("id")
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)  # Database record deleted
    db.session.commit()      # Files still on disk!
```

**Recommended Improvement**:
```python
import os
from flask import current_app

@blogpost_bp.route('/post/delete', methods=['POST'])
@login_required
def delete_post():
    post = BlogPost.query.get_or_404(request.form.get("id"))

    # Delete files from disk
    upload_folder = current_app.config['BLOG_POST_UPLOAD_FOLDER']
    if post.portrait:
        portrait_path = os.path.join(upload_folder, post.portrait)
        if os.path.exists(portrait_path):
            os.remove(portrait_path)

    if post.thumbnail:
        thumb_path = os.path.join(upload_folder, post.thumbnail)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

    # Delete database record
    db.session.delete(post)
    db.session.commit()

    flash('Post and images deleted!', 'success')
    return redirect(url_for('main_bp.index'))
```

---

## Troubleshooting

### Problem: "413 Request Entity Too Large"

**Cause**: Upload exceeds `MAX_CONTENT_LENGTH` (15MB)

**Solutions**:
1. Compress image before upload
2. Increase limit in `config.py`:
   ```python
   MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
   ```
3. Configure reverse proxy (Nginx):
   ```nginx
   client_max_body_size 50M;
   ```

### Problem: Uploaded files not persisting (Docker)

**Cause**: Volume not mounted or incorrect permissions

**Check**:
```bash
docker-compose exec flask-site ls -la /app/uploads/blog-posts/
```

**Fix**:
```yaml
# docker-compose.yml
volumes:
  - ./uploads:/app/uploads  # Ensure this line exists

# Rebuild and restart
docker-compose down
docker-compose up --build
```

### Problem: "Permission denied" when saving files

**Cause**: Upload directory not writable by flask user

**Fix (Docker)**:
```bash
# On host machine
sudo chown -R 1000:1000 uploads/

# Or in container
docker-compose exec flask-site chown -R flask:flask /app/uploads/
```

**Fix (Local)**:
```bash
chmod -R 755 uploads/
```

### Problem: Thumbnail not generating

**Cause**: PIL/Pillow not installed or image corrupted

**Check**:
```bash
docker-compose exec flask-site python -c "from PIL import Image; print('PIL OK')"
```

**Fix**:
```bash
pip install Pillow
# or
docker-compose exec flask-site pip install Pillow
```

### Problem: Files serve with wrong MIME type

**Cause**: Flask's `send_from_directory` guesses MIME type from extension

**Fix** (if needed):
```python
import mimetypes

@main_bp.route('/uploads/blog-posts/<filename>')
def uploaded_file(filename):
    mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    return send_from_directory(
        current_app.config['BLOG_POST_UPLOAD_FOLDER'],
        filename,
        mimetype=mimetype
    )
```

### Problem: Orphaned files accumulating

**Cause**: Files not deleted when posts are deleted

**Solution**: Implement file cleanup in delete route (see [Common Operations](#delete-post-orphaned-files))

**Find Orphaned Files**:
```bash
# List all files in uploads
ls uploads/blog-posts/

# Get all filenames from database
docker-compose exec flask-site python -c "
from app import create_app, db
from app.models import BlogPost
app = create_app()
with app.app_context():
    posts = BlogPost.query.all()
    for p in posts:
        print(p.portrait, p.thumbnail)
"

# Compare manually to find orphans
```

---

## Performance Considerations

### Thumbnail Generation

**Impact**: Synchronous processing blocks request

**Current Behavior**:
- Thumbnail generated during POST request
- User waits for image processing to complete
- For large images, may cause timeout

**Potential Improvements**:
1. **Async Processing** (Celery):
   ```python
   @celery.task
   def generate_thumbnail(post_id):
       # Generate thumbnail in background
       pass
   ```

2. **Pre-resize on Client**:
   - Use JavaScript to resize before upload
   - Reduce upload size and server processing

3. **Lazy Thumbnail Generation**:
   - Generate on first access, not upload
   - Cache generated thumbnails

### Disk Space Management

**Current**: No automated cleanup

**Recommendations**:
- Monitor disk usage: `df -h`
- Implement cleanup job for orphaned files
- Set up disk space alerts
- Consider object storage (S3) for production

---

## Future Enhancements

### Recommended Improvements

1. **File Type Validation** (magic bytes):
   ```python
   import imghdr

   if imghdr.what(file_path) not in ['jpeg', 'png']:
       raise ValidationError('Invalid image file')
   ```

2. **Image Optimization**:
   ```python
   img.save(path, optimize=True, quality=85)
   ```

3. **CDN Integration**:
   - Upload to S3/CloudFront
   - Reduce server bandwidth
   - Improve global delivery

4. **Multiple Image Sizes**:
   ```python
   sizes = [(300, 300), (600, 600), (1200, 1200)]
   for width, height in sizes:
       img_copy = img.copy()
       img_copy.thumbnail((width, height))
       img_copy.save(f"{base_name}_{width}x{height}.jpg")
   ```

5. **Automatic File Cleanup**:
   - Cascade delete files when post deleted
   - Background job to remove orphaned files

6. **Access Control**:
   - Require authentication for draft post images
   - Generate signed URLs with expiration

---

## Code References

**Upload Logic**: `app/routes_blogpost.py:38-70`
**File Validation**: `app/forms.py:45-46`
**Serve Files**: `app/routes.py:78-80`
**Config**: `config.py:18-19`
**Docker Volumes**: `docker-compose.yml:26-27`

---

## Summary

The file upload system provides secure image uploads with automatic thumbnail generation. Key features include filename sanitization, file extension validation, and PIL-based image processing. While functional, consider implementing file cleanup on post deletion, stronger validation, and async processing for production deployments.
