# Templates Context

## Purpose
Jinja2 HTML templates for server-side rendering. All templates follow template inheritance pattern with layout.html as base.

## Template Hierarchy

### Base Template
- **layout.html** - Master template with HTML structure, navigation, flash messages
  - Blocks: `{% block title %}`, `{% block js %}`, `{% block content %}`
  - Global features:
    - CSRF meta tag: `<meta name="csrf-token" content="{{ csrf_token() }}">`
    - jQuery + jQuery UI loaded
    - Material Symbols icons
    - Global AJAX CSRF setup via $.ajaxSetup()
    - Flash message system (server-side + JS addFlashMessage())
    - Sidebar navigation with toggle
    - Duolingo-style button CSS loaded

### Template Files

#### Public Pages
- **index.html** - Homepage with blog post listing
  - Extends: layout.html
  - Context vars: `blog_posts` (list), `current_user`, `current_page`
  - Features: Draft badges, edit/delete for authenticated, thumbnail display

- **about.html** - About page
  - Extends: layout.html
  - Includes: about_text.html (content partial)

- **contact.html** - Contact form
  - Extends: layout.html
  - Context vars: `form` (ContactForm), `current_page`
  - AJAX support: Form submission with JSON response

#### Blog Templates
- **view_post.html** - Single blog post view
  - Context vars: `post` (BlogPost object)
  - Features: Full content display, portrait image, timestamps, edit/delete controls

- **new_post.html** - Create blog post form
  - Context vars: `form` (BlogPostForm)
  - Features: Dual submit buttons (Save Draft, Publish), file upload fields
  - Security: CSRF token via `{{ form.csrf_token }}`

- **edit_post.html** - Edit existing blog post
  - Context vars: `form` (BlogPostForm), `post` (BlogPost)
  - Features: Pre-filled form, image preview, draft toggle

#### Authentication Templates
- **login.html** - User login form
  - Context vars: `registration_enabled` (bool)
  - Features: Link to registration if enabled

- **register.html** - User registration form
  - Features: Username/email/password fields, client-side validation

#### Profile Templates
- **profile.html** - User profile view
  - Context vars: `user` (User object), `blog_posts` (user's posts)
  - Features: Profile picture, bio, post listing

- **edit_profile.html** - Edit user profile
  - Context vars: `form` (ProfileEditForm), `current_user`
  - Features: Profile picture upload, bio editing

- **change_password.html** - Password change form
  - Context vars: `form` (ChangePasswordForm)
  - Security: Current password validation

#### Admin Templates
- **admin_dashboard.html** - Admin panel home
  - Context vars: `users` (list), `roles` (list), `stats` (dict)
  - Features: User management, role assignment, system stats

- **admin_edit_user.html** - Edit user (admin)
  - Context vars: `user`, `form`, `available_roles`
  - Features: Role assignment, account status toggle

- **admin_create_user.html** - Create user (admin)
  - Context vars: `form` (UserCreateForm)

- **admin_images.html** - Image management
  - Context vars: `images` (list of uploaded files)
  - Features: View/delete uploaded images

#### Minecraft Templates
- **mc.html** - Minecraft server RCON control panel
  - Context vars: `commands` (MinecraftCommand list)
  - Features: Command execution, player management, server status

## Jinja2 Patterns Used

### Template Inheritance
```jinja2
{% extends "layout.html" %}

{% block title %}Page Title{% endblock %}

{% block content %}
  <!-- Page content -->
{% endblock %}
```

### Conditional Rendering
```jinja2
{% if current_user.is_authenticated %}
  <a href="{{ url_for('auth.logout') }}">Logout</a>
{% else %}
  <a href="{{ url_for('auth.login') }}">Login</a>
{% endif %}
```

### Looping
```jinja2
{% for post in blog_posts %}
  <div>{{ post.title }}</div>
{% else %}
  <p>No posts available.</p>
{% endfor %}
```

### URL Generation
```jinja2
<a href="{{ url_for('blogpost.view_post', post_id=post.id) }}">Read more</a>
<img src="{{ url_for('static', filename='img/logo.png') }}" />
```

### Flash Messages (Server-Side)
```jinja2
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    {% for category, message in messages %}
      <div class="alert alert-{{ category }}">{{ message }}</div>
    {% endfor %}
  {% endif %}
{% endwith %}
```

### Forms with CSRF
```jinja2
<form method="POST">
  {{ form.hidden_tag() }}  <!-- Includes CSRF token -->
  {{ form.username.label }}
  {{ form.username(class="form-control") }}
  {{ form.submit() }}
</form>
```

### Custom Filters
```jinja2
{{ post.last_updated|localtime }}  <!-- Custom timezone filter -->
{{ post.content|safe }}  <!-- Render HTML without escaping -->
```

### Role-Based Display
```jinja2
{% if current_user.has_role('blogger') or current_user.is_admin() %}
  <a href="{{ url_for('blogpost.new_post') }}">New Post</a>
{% endif %}
```

## JavaScript Patterns

### jQuery Usage
**Project uses jQuery + jQuery UI. All JavaScript should use jQuery conventions.**

```javascript
// ✅ CORRECT - Use jQuery
$(document).ready(function() {
  $('#myButton').on('click', function() {
    // Handle click
  });
});

// ❌ AVOID - Vanilla JS (for consistency)
document.getElementById('myButton').addEventListener('click', function() {
  // Inconsistent with project
});
```

### AJAX Form Submission
```javascript
// Standard AJAX pattern with CSRF
$.ajax({
  url: "{{ url_for('route') }}",
  method: "POST",
  data: formData,
  success: function(response) {
    if (response.success) {
      addFlashMessage('success', response.message);
      window.location.href = response.redirect;
    } else {
      addFlashMessage('danger', response.error);
    }
  },
  error: function(xhr, status, error) {
    addFlashMessage('danger', 'An error occurred. Please try again.');
    console.error('AJAX error:', error);
  }
});
```

**AJAX Best Practices:**
- Always handle both `success` and `error` callbacks
- Use `addFlashMessage()` for user feedback
- Return JSON from routes: `return jsonify({'success': True, 'message': '...'})`
- CSRF token is automatically added via global `$.ajaxSetup()` in layout.html

### Flash Messages (Client-Side)
```javascript
// Add flash message from JavaScript
addFlashMessage('success', 'Operation completed!');
addFlashMessage('danger', 'An error occurred');
addFlashMessage('warning', 'Please review your input');
addFlashMessage('info', 'Information message');

// Available categories: success, danger, warning, info
// Messages appear in the #flash-messages container
```

### CSRF Token Retrieval
```javascript
// CSRF token from meta tag
let csrfToken = $("meta[name=csrf-token]").attr("content");

// Manual AJAX with CSRF
$.ajax({
  url: '/some/route',
  method: 'POST',
  headers: {
    'X-CSRFToken': csrfToken
  },
  data: { /* data */ }
});

// Note: Global $.ajaxSetup() already handles this automatically
```

### Event Handling Patterns
```javascript
// ✅ CORRECT - Delegated events for dynamic content
$(document).on('click', '.dynamic-button', function() {
  // Handles buttons added after page load
});

// ✅ CORRECT - Direct events for static content
$('#staticButton').on('click', function() {
  // For elements that exist on page load
});

// ❌ AVOID - Inline event handlers
<button onclick="handleClick()">Click</button>
```

### Form Validation (Client-Side)
```javascript
$('#myForm').on('submit', function(e) {
  // Validate before submission
  let isValid = true;

  if ($('#username').val().trim() === '') {
    addFlashMessage('danger', 'Username is required');
    isValid = false;
  }

  if (!isValid) {
    e.preventDefault();  // Prevent form submission
    return false;
  }

  // Allow form to submit
  return true;
});
```

### Common JavaScript Utilities
```javascript
// Redirect to URL
window.location.href = "{{ url_for('route') }}";

// Confirm before dangerous action
if (confirm('Are you sure you want to delete this?')) {
  // Proceed with deletion
}

// Toggle element visibility
$('#element').toggle();
$('#element').show();
$('#element').hide();

// Add/remove CSS classes
$('#element').addClass('active');
$('#element').removeClass('inactive');
$('#element').toggleClass('highlight');
```

## Styling Patterns

### Button Styling (clicky-buttons.css)
**Project uses custom clicky-button classes for consistent UI.**

**Available Classes:**
- `.clicky-primary` - Default actions (blue)
- `.clicky-success` - Publish/confirm actions (green)
- `.clicky-secondary` - Cancel/back actions (gray)
- `.clicky-draft` - Save as draft actions (yellow)
- `.clicky-danger` - Delete/destructive actions (red)

**CRITICAL**: Always use `<button>` elements, NOT `<a>` tags:
```html
<!-- ✅ CORRECT - Button elements -->
<button type="submit" class="clicky-success">Publish</button>
<button type="submit" name="action" value="draft" class="clicky-draft">Save Draft</button>
<button type="button" onclick="location.href='{{ url_for('route') }}'" class="clicky-secondary">Cancel</button>

<!-- ❌ INCORRECT - Link elements render incorrectly -->
<a href="..." class="clicky-primary">Button</a>
```

**Button Usage Guidelines:**

| Action Type | Class | Element | Example |
|-------------|-------|---------|---------|
| Submit form | `clicky-primary` | `<button type="submit">` | Create Post |
| Confirm/Publish | `clicky-success` | `<button type="submit">` | Publish |
| Save draft | `clicky-draft` | `<button type="submit">` | Save as Draft |
| Cancel/Back | `clicky-secondary` | `<button type="button">` | Cancel |
| Delete | `clicky-danger` | `<button type="submit">` | Delete |

**Navigation Buttons:**
```html
<!-- For navigation (not form submission) -->
<button type="button" class="clicky-secondary" onclick="window.location.href='{{ url_for('main.index') }}'">
  Back to Home
</button>
```

**Dual Submit Buttons (Draft Pattern):**
```html
<form method="POST">
  {{ form.hidden_tag() }}

  <!-- Form fields -->
  {{ form.title(class="form-control") }}
  {{ form.content(class="form-control") }}

  <!-- Dual submit buttons -->
  <button type="submit" name="action" value="draft" class="clicky-draft">Save as Draft</button>
  <button type="submit" name="action" value="publish" class="clicky-success">Publish</button>
</form>
```

**In routes, handle dual submit:**
```python
@blogpost_bp.route('/post/new', methods=['POST'])
def new_post():
    action = request.form.get('action')

    if action == 'draft':
        post.is_draft = True
    else:  # publish
        post.is_draft = False

    db.session.commit()
```

### Status Badges

#### Draft Badge
```html
{% if post.is_draft %}
<span class="draft-badge">DRAFT</span>
{% endif %}
```

#### Custom Status Badges
```html
<!-- Success badge -->
<span class="badge badge-success">Published</span>

<!-- Warning badge -->
<span class="badge badge-warning">Pending</span>

<!-- Danger badge -->
<span class="badge badge-danger">Archived</span>
```

### Form Styling
```html
<!-- Standard form input -->
<div class="form-group">
  {{ form.username.label(class="form-label") }}
  {{ form.username(class="form-control", placeholder="Enter username") }}

  {% if form.username.errors %}
    <div class="form-error">
      {{ form.username.errors[0] }}
    </div>
  {% endif %}
</div>
```

### CSS Class Naming Conventions
**Follow BEM-like naming for custom classes:**
```css
/* Block */
.blog-post { }

/* Element */
.blog-post__title { }
.blog-post__content { }

/* Modifier */
.blog-post--draft { }
.blog-post--featured { }
```

### Responsive Design
```html
<!-- Mobile-friendly layouts -->
<div class="container">
  <div class="row">
    <div class="col-md-8">
      <!-- Main content -->
    </div>
    <div class="col-md-4">
      <!-- Sidebar -->
    </div>
  </div>
</div>
```

### Icons (Material Symbols)
```html
<!-- Material Symbols icons are loaded globally -->
<span class="material-symbols-outlined">
  edit
</span>

<span class="material-symbols-outlined">
  delete
</span>

<span class="material-symbols-outlined">
  visibility
</span>
```

## Security Considerations

### XSS Prevention
- **Default**: Auto-escaping enabled (safe by default)
- **Unsafe content**: Use `|safe` filter ONLY for trusted HTML
- **User input**: Never use `|safe` on user-generated content

### CSRF Protection
- All forms MUST include: `{{ form.hidden_tag() }}`
- AJAX requests: CSRF token automatically added via $.ajaxSetup()

### Jinja2 Syntax Limitations
**CANNOT use Jinja2 in HTML attribute values**:
```html
<!-- INCORRECT -->
<input value="{{ post.title }}">

<!-- CORRECT -->
{% if post %}
<input value="{{ post.title }}">
{% endif %}
```

## Template Context Variables

### Always Available (via Flask globals)
- `current_user` - Logged-in user or AnonymousUser
- `url_for()` - Generate URLs for routes
- `get_flashed_messages()` - Retrieve flash messages
- `csrf_token()` - Generate CSRF token

### Commonly Passed Variables
- `form` - WTForms form object
- `current_page` - Active navigation item
- `blog_posts` - List of BlogPost objects
- `post` - Single BlogPost object
- `user` - User profile object
- `registration_enabled` - Boolean from config

## Agent Touchpoints

### frontend-developer
- Needs: Template structure, context variables, JavaScript patterns, styling classes
- Common tasks: Creating new templates, adding AJAX functionality, implementing UI components
- Key files: layout.html, new templates, static/css/*, static/js/*

### backend-architect
- Needs: Template inheritance pattern, context variable expectations
- Common tasks: Planning what data routes should pass to templates
- Key files: All templates for understanding view requirements

### security-auditor
- Needs: CSRF implementation, XSS prevention, safe filter usage
- Common tasks: Auditing user input rendering, validating CSRF in forms, checking |safe usage
- Key files: Forms templates, user-generated content displays

### documentation-expert
- Needs: Template structure, available blocks, context variables
- Common tasks: Documenting template usage, creating style guides
- Key files: layout.html (base structure), example templates

## Common Tasks

### Creating a New Template
1. Create file in `app/templates/`
2. Extend layout: `{% extends "layout.html" %}`
3. Define title block: `{% block title %}Page Title{% endblock %}`
4. Define content block: `{% block content %}...{% endblock %}`
5. Add route in appropriate blueprint to render it

### Adding a Form
1. Define form in `app/forms.py`
2. Pass form to template from route: `render_template('template.html', form=form)`
3. Render in template:
```jinja2
<form method="POST">
  {{ form.hidden_tag() }}
  {{ form.field_name.label }}
  {{ form.field_name(class="css-class") }}
  {% if form.field_name.errors %}
    <span class="error">{{ form.field_name.errors[0] }}</span>
  {% endif %}
  {{ form.submit(class="duolingo-primary") }}
</form>
```

### Adding AJAX Functionality
1. Add CSRF meta tag (already in layout.html)
2. Write AJAX handler in template's `{% block js %}`
3. Use `addFlashMessage()` for user feedback
4. Route should return JSON: `return jsonify({'success': True})`

### Displaying Draft Badge
```jinja2
{% if current_user.is_authenticated and object.is_draft %}
<div class="draft-badge">DRAFT</div>
{% endif %}
```

### Role-Based UI Elements
```jinja2
{% if current_user.has_role('admin') %}
  <!-- Admin-only content -->
{% endif %}

{% if current_user.has_any_role(['blogger', 'admin']) %}
  <!-- Blogger or admin content -->
{% endif %}
```

## Frontend Best Practices

### Template Variable Naming
```jinja2
{# ✅ GOOD - Descriptive names #}
{{ blog_posts }}
{{ current_user }}
{{ form_data }}

{# ❌ BAD - Vague names #}
{{ posts }}
{{ user }}
{{ data }}
```

### Conditional Logic
```jinja2
{# ✅ GOOD - Clear conditions #}
{% if current_user.is_authenticated and post.is_draft %}
  <span class="draft-badge">DRAFT</span>
{% endif %}

{# ✅ GOOD - Negative conditions #}
{% if not current_user.has_role('admin') %}
  <p>Access denied</p>
{% endif %}
```

### Loop Performance
```jinja2
{# ✅ GOOD - Check before looping #}
{% if blog_posts %}
  {% for post in blog_posts %}
    {{ post.title }}
  {% endfor %}
{% else %}
  <p>No posts available.</p>
{% endif %}

{# Also acceptable - loop.else #}
{% for post in blog_posts %}
  {{ post.title }}
{% else %}
  <p>No posts available.</p>
{% endfor %}
```

### DRY Principle (Don't Repeat Yourself)
```jinja2
{# ✅ GOOD - Use macros for repeated HTML #}
{% macro render_button(text, type='primary', action='submit') %}
  <button type="{{ action }}" class="clicky-{{ type }}">{{ text }}</button>
{% endmacro %}

{{ render_button('Save', 'success') }}
{{ render_button('Cancel', 'secondary', 'button') }}

{# ✅ GOOD - Use includes for partials #}
{% include 'partials/flash_messages.html' %}
```

### Accessibility
```html
<!-- ✅ GOOD - Include labels -->
<label for="username">Username</label>
<input type="text" id="username" name="username">

<!-- ✅ GOOD - ARIA attributes for screen readers -->
<button aria-label="Delete post">
  <span class="material-symbols-outlined">delete</span>
</button>

<!-- ✅ GOOD - Alt text for images -->
<img src="{{ post.portrait }}" alt="{{ post.title }}">
```

### Performance Considerations
```jinja2
{# Minimize database queries in templates #}
{# ✅ GOOD - Pass data from route #}
{% for post in blog_posts %}
  {{ post.author.username }}  {# ✓ If using joinedload in route #}
{% endfor %}

{# ❌ BAD - N+1 query problem #}
{% for post in blog_posts %}
  {{ post.author.query.first().username }}  {# ✗ Queries database in loop #}
{% endfor %}
```

### Template Debugging
```jinja2
{# Debug variable output (development only) #}
<pre>{{ blog_posts|pprint }}</pre>

{# Check if variable exists #}
{% if post is defined %}
  {{ post.title }}
{% endif %}

{# Debug filters #}
{{ post.date_posted|string }}  {# Convert to string to inspect #}
```

## Common Patterns

### Flash Message Display
```jinja2
{# In layout.html (already implemented) #}
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div id="flash-messages">
      {% for category, message in messages %}
        <div class="alert alert-{{ category }}">{{ message }}</div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}
```

### Pagination (Future Enhancement)
```jinja2
{# Example pagination pattern #}
<div class="pagination">
  {% if posts.has_prev %}
    <a href="{{ url_for('main.index', page=posts.prev_num) }}">Previous</a>
  {% endif %}

  <span>Page {{ posts.page }} of {{ posts.pages }}</span>

  {% if posts.has_next %}
    <a href="{{ url_for('main.index', page=posts.next_num) }}">Next</a>
  {% endif %}
</div>
```

### Image Display with Fallback
```jinja2
{# Blog post with optional portrait #}
{% if post.portrait %}
  <img src="{{ url_for('main.uploaded_file', filename=post.portrait) }}"
       alt="{{ post.title }}"
       onerror="this.src='/static/img/default-post.png'">
{% else %}
  <img src="/static/img/default-post.png" alt="Default image">
{% endif %}
```

### Dynamic Form Actions
```jinja2
{# Form that submits to different routes based on context #}
<form method="POST" action="{{ url_for('blogpost.edit_post', post_id=post.id) if post else url_for('blogpost.new_post') }}">
  {{ form.hidden_tag() }}
  {# Form fields #}
</form>
```

## Troubleshooting

### Common Template Errors

**Error:** `jinja2.exceptions.UndefinedError: 'post' is undefined`
- **Cause:** Variable not passed from route
- **Solution:** Add variable to `render_template()` call

**Error:** `TemplateSyntaxError: expected token 'end of statement block', got 'is'`
- **Cause:** Invalid Jinja2 syntax in attribute
- **Solution:** Move Jinja2 logic outside HTML attributes

**Error:** CSRF token missing
- **Cause:** Missing `{{ form.hidden_tag() }}` in form
- **Solution:** Add `form.hidden_tag()` immediately after `<form>` tag

**Error:** Static files not loading (404)
- **Cause:** Incorrect path in `url_for('static', filename='...')`
- **Solution:** Verify file exists in `app/static/` and path is correct

### Template Debugging Tips
```python
# In route - pass debug info
return render_template('template.html',
                      debug=app.config['DEBUG'],
                      all_vars=locals())  # All local variables
```

```jinja2
{# In template - display all passed variables #}
{% if debug %}
  <pre>{{ all_vars|pprint }}</pre>
{% endif %}
```

## Related Directories
- `app/routes/*.py` - Routes that render these templates
- `app/forms/*.py` - Form objects passed to templates
- `app/static/` - CSS, JavaScript, images referenced in templates
- `app/utils/filters.py` - Custom Jinja2 filters (|localtime, etc.)

## Custom Filters Available
- `|localtime` - Convert UTC datetime to configured timezone
- `|safe` - Mark string as safe HTML (USE CAREFULLY - see docs/SECURITY.md)
- Standard Jinja2 filters: `|length`, `|lower`, `|upper`, `|title`, `|tojson`, `|pprint`, etc.

## Block Structure in layout.html
```jinja2
{% block title %}Default Title{% endblock %}
{% block js %}<!-- Additional JavaScript -->{% endblock %}
{% block content %}<!-- Main page content -->{% endblock %}
```

## Related Documentation
- `docs/SECURITY.md` - XSS prevention, CSRF protection, safe filter usage
- `app/routes/CONTEXT.md` - Route naming and structure
- `app/static/CONTEXT.md` - Static file organization
- `CLAUDE.md` - Development workflow and agent usage
