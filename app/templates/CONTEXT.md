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

### AJAX Form Submission
```javascript
$.ajax({
  url: "{{ url_for('route') }}",
  method: "POST",
  data: formData,
  success: function(response) {
    if (response.success) {
      window.location.href = response.redirect;
    }
  }
});
```

### Flash Messages (Client-Side)
```javascript
addFlashMessage('success', 'Operation completed!');
// Available categories: success, danger, warning, info
```

### CSRF Token Retrieval
```javascript
let csrfToken = $("meta[name=csrf-token]").attr("content");
xhr.setRequestHeader("X-CSRFToken", csrfToken);
```

## Styling Patterns

### Duolingo Button Classes
- `.duolingo-primary` - Default actions (blue)
- `.duolingo-success` - Publish/confirm actions (green)
- `.duolingo-secondary` - Cancel/back actions (gray)
- `.duolingo-draft` - Save as draft actions (yellow)
- `.duolingo-danger` - Delete/destructive actions (red)

**IMPORTANT**: Use `<button>` tags, not `<a>` tags for proper styling:
```html
<!-- CORRECT -->
<button type="submit" class="duolingo-success">Publish</button>
<button type="button" onclick="location.href='...'" class="duolingo-secondary">Cancel</button>

<!-- INCORRECT (renders with link styling) -->
<a href="..." class="duolingo-primary">Button</a>
```

### Draft Badge
```html
{% if post.is_draft %}
<div class="draft-badge">DRAFT</div>
{% endif %}
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

## Related Directories
- `/app/routes_*.py` - Routes that render these templates
- `/app/forms.py` - Form objects passed to templates
- `/app/static/` - CSS, JavaScript, images referenced in templates
- `/app/filters.py` - Custom Jinja2 filters (|localtime, etc.)

## Custom Filters Available
- `|localtime` - Convert UTC datetime to configured timezone
- `|safe` - Mark string as safe HTML (USE CAREFULLY)
- Standard Jinja2 filters: `|length`, `|lower`, `|upper`, `|title`, etc.

## Block Structure in layout.html
```jinja2
{% block title %}Default Title{% endblock %}
{% block js %}<!-- Additional JavaScript -->{% endblock %}
{% block content %}<!-- Main page content -->{% endblock %}
```
