# Uploads Directory Context

## Purpose
User-uploaded files directory. Contains blog post images (portrait and thumbnails) and user profile pictures. This directory is NOT version controlled (.gitignore'd).

## Directory Structure

```
uploads/
├── blog-posts/    - Blog post images (portraits and auto-generated thumbnails)
└── profiles/      - User profile pictures
```

## Subdirectories

### blog-posts/
**Purpose**: Store blog post portrait images and thumbnails

**File Types**: JPG, PNG, JPEG (validated via magic numbers, not just extension)

**Upload Process**:
1. User uploads portrait via BlogPostForm
2. File validated by `validate_image_file()`:
   - Checks magic numbers (not just extension)
   - Validates file size (< 5MB per MAX_CONTENT_LENGTH)
   - Checks for malicious content
3. Filename sanitized via `sanitize_filename()` + `secure_filename()`
4. Portrait saved to this directory
5. Thumbnail auto-generated (300x300) or custom uploaded
6. Both filenames stored in BlogPost.portrait and BlogPost.thumbnail

**Security**:
- Files served via `send_from_directory()` (prevents path traversal)
- Route: `GET /uploads/blog-posts/<filename>` in routes.py
- Only authenticated bloggers/admins can upload
- File type validation via Pillow (opens image to verify)

**Naming Pattern**:
- Original: `{sanitized_filename}.{ext}`
- Thumbnail: `{sanitized_filename}.{ext}` (if auto-generated, named same as portrait)

**Cleanup**:
- When blog post deleted: Associated images removed from filesystem
- Orphaned files possible if deletion fails mid-process

### profiles/
**Purpose**: Store user profile pictures

**File Types**: JPG, PNG, JPEG (validated)

**Upload Process**:
1. User uploads via ProfileEditForm
2. Same validation as blog-posts (magic numbers, size, content)
3. Filename sanitized and secured
4. Saved to this directory
5. Filename stored in User.profile_picture

**Security**:
- Same validation and serving pattern as blog-posts
- Only authenticated users can upload own profile picture
- Cannot upload to other users' profiles

**Naming Pattern**:
- Format: `{user_id}_{timestamp}.{ext}` or `{sanitized_filename}.{ext}`

**Cleanup**:
- When user changes profile picture: Old picture should be deleted
- When user deleted: Profile picture should be cleaned up

## Configuration (from config.py)

```python
BLOG_POST_UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads/blog-posts')
PROFILE_UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads/profiles')
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB limit
```

**Directory Creation**: Automatically created in `app/__init__.py` create_app():
```python
os.makedirs(app.config['PROFILE_UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
```

## File Validation Pattern

### validate_image_file(file) → (bool, error_msg)
**Location**: `app/utils/file_validation.py`

**Checks**:
1. **File size**: Must be < MAX_CONTENT_LENGTH
2. **Magic number validation**: Reads first bytes to verify file type
   - PNG: `\x89PNG\r\n\x1a\n`
   - JPEG: `\xff\xd8\xff`
   - GIF: `GIF87a` or `GIF89a`
3. **Content validation**: Opens with Pillow to ensure valid image
4. **Extension check**: Must be in allowed extensions (jpg, png, jpeg)

**Returns**:
- `(True, None)` if valid
- `(False, "Error message")` if invalid

### sanitize_filename(filename) → str
**Location**: `app/utils/file_validation.py`

**Process**:
1. Removes special characters
2. Replaces spaces with underscores
3. Converts to lowercase
4. Preserves extension

**Then wrapped with**:
```python
from werkzeug.utils import secure_filename
safe_name = secure_filename(sanitize_filename(original_name))
```

## Serving Files

### Blog Post Images
```python
@main_bp.route('/uploads/blog-posts/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['BLOG_POST_UPLOAD_FOLDER'], filename)
```

**Usage in templates**:
```jinja2
<img src="{{ url_for('main_bp.uploaded_file', filename=post.portrait) }}" />
<img src="{{ url_for('main_bp.uploaded_file', filename=post.thumbnail) }}" />
```

### Profile Pictures
Similar pattern (route in routes_profile.py):
```python
@profile_bp.route('/uploads/profiles/<filename>')
def profile_picture(filename):
    return send_from_directory(current_app.config['PROFILE_UPLOAD_FOLDER'], filename)
```

## Security Best Practices

### ✅ Implemented
1. **Magic number validation** - Not just extension checking
2. **File size limits** - 5MB max via MAX_CONTENT_LENGTH
3. **Secure filename** - Prevents path traversal with secure_filename()
4. **Sanitization** - Removes special characters before securing
5. **send_from_directory** - Flask's safe file serving method
6. **Authentication required** - Only logged-in users can upload
7. **Authorization** - Users can only upload to their own profiles
8. **Content validation** - Pillow opens image to verify it's real

### ⚠️ Considerations
1. **Orphaned files** - Failed deletions can leave files on disk
2. **Storage limits** - No quota enforcement per user
3. **No virus scanning** - Relies on file type validation only
4. **No rate limiting** - Users could spam uploads
5. **Filename collisions** - Same filename overwrites (use unique naming)

## Common Issues

### Upload Fails
**Causes**:
- File too large (> 5MB)
- Invalid file type (not JPG/PNG)
- Corrupted image file
- Directory permissions

**Solutions**:
- Check MAX_CONTENT_LENGTH
- Verify magic numbers match file type
- Test with Pillow locally
- Ensure uploads/ directory writable

### Image Not Displaying
**Causes**:
- Filename mismatch in database
- File deleted from filesystem
- Route not registered
- Permission issues

**Solutions**:
- Check BlogPost.portrait/thumbnail values
- Verify file exists on disk
- Ensure route registered in __init__.py
- Check directory permissions

### Thumbnail Generation Fails
**Causes**:
- Pillow not installed
- Invalid image format
- Insufficient permissions
- Disk space full

**Solutions**:
- Install Pillow: `pip install Pillow`
- Verify source image is valid
- Check directory permissions
- Monitor disk space

## File Cleanup Patterns

### On Blog Post Deletion
```python
@blogpost_bp.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)

    # Delete files from filesystem
    if post.portrait:
        portrait_path = os.path.join(current_app.config['BLOG_POST_UPLOAD_FOLDER'], post.portrait)
        if os.path.exists(portrait_path):
            os.remove(portrait_path)

    if post.thumbnail:
        thumbnail_path = os.path.join(current_app.config['BLOG_POST_UPLOAD_FOLDER'], post.thumbnail)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

    # Delete database record
    db.session.delete(post)
    db.session.commit()
```

### On Profile Picture Change
```python
# Before saving new picture
if current_user.profile_picture:
    old_path = os.path.join(current_app.config['PROFILE_UPLOAD_FOLDER'],
                            current_user.profile_picture)
    if os.path.exists(old_path):
        os.remove(old_path)

# Save new picture
current_user.profile_picture = new_filename
```

## Agent Touchpoints

### backend-architect
- Needs: Upload patterns, file validation logic, serving routes
- Common tasks: Designing new upload features, planning storage strategies
- Key concerns: Security, validation, cleanup patterns

### python-pro
- Needs: File I/O patterns, Pillow usage, filesystem operations
- Common tasks: Optimizing image processing, implementing validation
- Key files: routes_blogpost.py, routes_profile.py, utils/file_validation.py

### security-auditor
- Needs: File validation implementation, serving routes, access controls
- Common tasks: Auditing upload security, reviewing file handling, checking path traversal prevention
- Key concerns: Magic number validation, secure_filename usage, authorization

### frontend-developer
- Needs: File upload forms, image display patterns, error handling
- Common tasks: Creating upload UI, displaying images, handling upload errors
- Key files: Templates with file upload forms, image display templates

## Common Tasks

### Adding New Upload Type
1. Create new subdirectory in uploads/
2. Add config variable in config.py
3. Create directory in create_app() (app/__init__.py)
4. Add validation function in utils/file_validation.py
5. Create upload route with validation
6. Create serving route with send_from_directory
7. Add cleanup logic on deletion

### Implementing File Quota
```python
# In upload route
user_upload_size = sum(os.path.getsize(f) for f in user_files)
if user_upload_size + new_file_size > USER_QUOTA:
    flash('Upload quota exceeded', 'danger')
    return redirect(...)
```

### Adding Image Processing
```python
from PIL import Image

# Resize image
img = Image.open(file_path)
img.thumbnail((800, 800))
img.save(file_path, optimize=True, quality=85)

# Convert format
img = img.convert('RGB')
img.save(new_path, 'JPEG', quality=90)
```

### Bulk Cleanup Script
```python
# Find orphaned files (not in database)
db_files = {post.portrait for post in BlogPost.query.all()}
disk_files = set(os.listdir(BLOG_POST_UPLOAD_FOLDER))
orphaned = disk_files - db_files

for orphan in orphaned:
    os.remove(os.path.join(BLOG_POST_UPLOAD_FOLDER, orphan))
```

## Related Files
- `/app/routes_blogpost.py` - Blog post upload/serve routes
- `/app/routes_profile.py` - Profile picture upload/serve routes
- `/app/forms.py` - FileField definitions with FileAllowed validators
- `/app/utils/file_validation.py` - Validation and sanitization functions
- `/config.py` - Upload folder paths and size limits

## .gitignore
This directory should be in .gitignore:
```
uploads/
!uploads/.gitkeep
```

Reasoning:
- User-uploaded content should not be version controlled
- Each environment (dev/staging/prod) has its own uploads
- Prevents repo bloat from binary image files
- Uploads managed separately (backups, CDN sync, etc.)

## Backup Considerations
- **Not version controlled** - Must be backed up separately
- **Production**: Should sync to S3/CDN for redundancy
- **Development**: Can be reset/cleared freely
- **Staging**: Should mirror production for testing

## Future Enhancements
Consider adding:
- CDN integration (S3, CloudFront)
- Image optimization pipeline
- Virus scanning
- Per-user storage quotas
- Rate limiting on uploads
- Unique filename generation (UUID-based)
- Automatic orphan cleanup job
- Image metadata stripping (EXIF removal)
- WebP format support
- Lazy loading optimization
