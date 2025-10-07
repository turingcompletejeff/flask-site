# Static Directory Context

## Purpose
Static assets served by Flask: CSS stylesheets, JavaScript files, images, and JSON data. All files served via `url_for('static', filename='path/to/file')`.

## Directory Structure

```
static/
├── css/          - Stylesheets
├── js/           - JavaScript files and libraries
├── img/          - Images and icons
└── json/         - Static JSON data files
```

## CSS Directory (`/static/css/`)

### Files
- **styles.css** - Main site stylesheet
  - Layout: Grid-based with sidebar navigation
  - Components: Blog posts, forms, flash messages, buttons
  - Responsive: Mobile-first design with media queries
  - Theme: Dark mode with custom color variables

- **duolingo-buttons.css** - Duolingo-style button system
  - Classes:
    - `.duolingo-primary` - Default actions (blue)
    - `.duolingo-success` - Publish/confirm (green)
    - `.duolingo-secondary` - Cancel/back (gray)
    - `.duolingo-draft` - Save draft (yellow)
    - `.duolingo-danger` - Delete/destructive (red)
  - **IMPORTANT**: Must use `<button>` elements, not `<a>` tags

### Usage Pattern
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/duolingo-buttons.css') }}">
```

## JavaScript Directory (`/static/js/`)

### Files
- **sidebar.js** - Sidebar navigation toggle functionality
  - Handles sidebar open/close
  - Mobile responsive behavior
  - Persists state

- **contact-form.js** - Contact form AJAX submission
  - Validates form before submit
  - Sends AJAX POST request
  - Handles success/error responses
  - Uses global CSRF setup from layout.html

- **phone-mask.js** - Phone number input masking
  - Formats phone input as (XXX) XXX-XXXX
  - Client-side validation
  - Works with ContactForm validation

### Libraries
- **jquery-ui-1.14.0.custom/** - jQuery UI components
  - jquery-ui.min.js - Core library
  - jquery-ui.min.css - Styles
  - jquery-ui.structure.min.css - Structure
  - jquery-ui.theme.min.css - Theme
  - Used for: Dialogs, datepickers, autocomplete

### Usage Pattern
```html
<script src="{{ url_for('static', filename='js/sidebar.js') }}"></script>
<script src="{{ url_for('static', filename='js/contact-form.js') }}"></script>
```

### JavaScript Patterns

#### CSRF-Protected AJAX
```javascript
// CSRF token already configured globally in layout.html
$.ajax({
  url: "/endpoint",
  method: "POST",
  data: { key: "value" },
  success: function(response) {
    addFlashMessage('success', 'Done!');
  }
});
```

#### Flash Messages (Client-Side)
```javascript
addFlashMessage(category, message);
// Categories: 'success', 'danger', 'warning', 'info'
```

## Images Directory (`/static/img/`)

### Icons & Branding
- **InBug-Black.png** - LinkedIn icon (black)
- **InBug-White.png** - LinkedIn icon (white)
- **LI-In-Bug.png** - LinkedIn icon (blue)
- **github-mark.png** - GitHub icon (black)
- **github-mark-white.png** - GitHub icon (white)
- **gmail-*.png** - Email icons (various styles)

### Banner Images
- **yurt-banner.webp** - Site header banner image

### Favicons (`/static/img/favicon_io/`)
- **favicon.ico** - Browser favicon
- **apple-touch-icon.png** - iOS home screen icon
- **favicon-16x16.png** - 16px favicon
- **favicon-32x32.png** - 32px favicon
- **android-chrome-192x192.png** - Android icon (192px)
- **android-chrome-512x512.png** - Android icon (512px)
- **site.webmanifest** - PWA manifest file

### Usage Pattern
```html
<img src="{{ url_for('static', filename='img/yurt-banner.webp') }}" alt="Banner">
<link rel="icon" type="image/png" sizes="32x32"
      href="{{ url_for('static', filename='img/favicon_io/favicon-32x32.png') }}">
```

## JSON Directory (`/static/json/`)
Static JSON data files for client-side data loading.

### Usage Pattern
```javascript
$.getJSON("{{ url_for('static', filename='json/data.json') }}", function(data) {
  // Process data
});
```

## Asset Loading Best Practices

### CSS Loading Order
1. External libraries (jQuery UI CSS)
2. Google Fonts
3. styles.css (main styles)
4. duolingo-buttons.css (component styles)

### JavaScript Loading Order
1. jQuery (from CDN)
2. jQuery UI
3. Custom scripts (sidebar, contact-form, etc.)

### Image Optimization
- Use WebP format for banners/photos
- PNG for icons with transparency
- SVG preferred for vector graphics
- Favicon sizes: 16x16, 32x32, 192x192, 512x512

## Security Considerations

### Static File Serving
- Flask serves static files automatically
- No direct filesystem access from client
- Path traversal prevented by Flask

### CSRF in AJAX
- Global CSRF setup in layout.html
- All AJAX requests automatically include token
- No manual token handling needed in JS files

### Image Uploads
- User uploads go to `/uploads/`, NOT `/static/`
- Static directory is for application assets only
- Never allow user-uploaded files in static/

## Agent Touchpoints

### frontend-developer
- Needs: CSS structure, JavaScript patterns, component styles, jQuery UI widgets
- Common tasks: Adding new styles, writing client-side logic, creating UI components
- Key files: styles.css, duolingo-buttons.css, custom JS files

### security-auditor
- Needs: AJAX CSRF implementation, static file serving configuration
- Common tasks: Auditing client-side validation, reviewing AJAX security, checking file access
- Key files: JavaScript files with AJAX, static file references

### documentation-expert
- Needs: Asset organization, loading patterns, available icons
- Common tasks: Documenting styling conventions, JavaScript API patterns
- Key files: All CSS/JS files for reference documentation

## Common Tasks

### Adding New Stylesheet
1. Create CSS file in `/app/static/css/`
2. Add to layout.html:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/new-styles.css') }}">
```

### Adding New JavaScript File
1. Create JS file in `/app/static/js/`
2. Add to template (in `{% block js %}`):
```html
<script src="{{ url_for('static', filename='js/new-script.js') }}"></script>
```

### Adding New Icon/Image
1. Place image in `/app/static/img/`
2. Reference in template:
```html
<img src="{{ url_for('static', filename='img/icon.png') }}" alt="Description">
```

### Creating Duolingo-Style Button
```html
<!-- Correct: Use <button> element -->
<button type="submit" class="duolingo-success">Publish</button>
<button type="button" onclick="location.href='...'" class="duolingo-secondary">Cancel</button>

<!-- Incorrect: Don't use <a> tags -->
<a href="..." class="duolingo-primary">Button</a>  <!-- Renders incorrectly -->
```

### Adding AJAX Functionality
1. Ensure CSRF token exists (already in layout.html)
2. Write AJAX handler:
```javascript
$.ajax({
  url: "{{ url_for('blueprint.route') }}",
  method: "POST",
  data: formData,
  success: function(response) {
    if (response.success) {
      addFlashMessage('success', response.message);
    }
  },
  error: function() {
    addFlashMessage('danger', 'An error occurred');
  }
});
```

### Using jQuery UI Components
```html
<!-- Include jQuery UI CSS and JS (already in layout.html) -->
<script>
$(document).ready(function() {
  $("#datepicker").datepicker();
  $("#dialog").dialog({
    autoOpen: false,
    modal: true
  });
});
</script>
```

## External Dependencies

### CDN Resources (loaded in layout.html)
- jQuery 3.7.1
- Material Symbols (Google Fonts icons)
- Google Fonts (Share Tech, Share Tech Mono, Texturina)

### Local Libraries
- jQuery UI 1.14.0 (custom build)

## File Naming Conventions
- CSS: kebab-case (duolingo-buttons.css)
- JavaScript: kebab-case (contact-form.js)
- Images: kebab-case or PascalCase for branding (yurt-banner.webp, InBug-White.png)

## Related Directories
- `/app/templates/` - Templates that reference these static files
- `/uploads/` - User-uploaded files (separate from static assets)

## Global JavaScript Functions (from layout.html)
- `addFlashMessage(category, message)` - Display flash message to user
  - Categories: 'success', 'danger', 'warning', 'info'
  - Auto-dismisses after 3 seconds

## CSRF Token Access
```javascript
// Available globally via meta tag
let csrfToken = $("meta[name=csrf-token]").attr("content");

// Automatically included in all AJAX requests via $.ajaxSetup()
```
