---
# yaml-language-server: $schema=schemas\claude_instruction.schema.json
Object type:
    - Claude Instruction
Creation date: "2025-10-07T23:55:14Z"
Created by:
    - jeff
id: bafyreida7ftaiuwrvrdemkfnk7wks2ckkhr3s5lsd6ld35tfjag2oyjmzu
---
# TC-48 plan   
## 🎯 Objective   
Restructure the Flask application to follow a modular, scalable architecture by organizing models and routes into dedicated directories with proper separation of concerns.   
## 🚀 JIRA Smart Commits Integration   
### Branch Naming Convention   
```
git checkout -b refactor/TC-48

```
### Commit Message Format   
Always start commits with ticket number for Smart Commits:   
   
# Basic commit   
git commit -m "TC-48Create models directory structure"   
# With time tracking   
git commit -m "TC-48 #time 1h Split models into separate files"   
# With comment   
git commit -m "TC-48 #comment Migrated all route files to routes/ directory"   
# When completing   
git commit -m "TC-48 #close #time 30m #comment Directory refactor complete and tested"

   
## 📋 Current State Analysis   
### Existing Structure   
\`\`\`
app/
├── \_\_init\_\_.py
├── models.py # All models in one file
├── routes.py # Main routes
├── routes\_auth.py # Auth routes
├── routes\_blogpost.py # Blog routes
├── routes\_mc.py # Minecraft routes
├── routes\_admin.py # Admin routes
├── routes\_health.py # Health check routes
├── routes\_profile.py # Profile routes
├── forms.py
├── filters.py
├── utils/
│ ├── file\_validation.py
│ ├── image\_utils.py
│ └── pagination.py
├── templates/
└── static/
\`\`\`   
### Current Models (in models.py)   
- \*\*User\*\* + \*\*Role\*\* (authentication and authorization)   
- \*\*BlogPost\*\* (blog content)   
- \*\*MinecraftCommand\*\* (game server integration)   
- \*\*StringArray\*\* (helper TypeDecorator)   
- \*\*role\_assignments\*\* (association table)   
   
### Current Routes Files   
1. \`routes.py\` - Main/blog listing, about, contact   
2. \`routes\_auth.py\` - Login, register, logout   
3. \`routes\_blogpost.py\` - CRUD operations for posts   
4. \`routes\_mc.py\` - Minecraft server integration   
5. \`routes\_admin.py\` - Admin dashboard and user management   
6. \`routes\_health.py\` - Health check endpoint   
7. \`routes\_profile.py\` - User profile management   
   
## 🛠️ Implementation Plan   
### Phase 1: Create Directory Structure (15 min)   
\*\*1.1 Create directories:\*\*
\`\`\`bash
mkdir -p app/models
mkdir -p app/routes
\`\`\`   
\*\*1.2 Create \`\_\_init\_\_.py\` files:\*\*   
- \`app/models/\_\_init\_\_.py\` - Export all models   
- \`app/routes/\_\_init\_\_.py\` - Export all blueprints   
   
### Phase 2: Split and Migrate Models (45 min)   
\*\*2.1 Create \`app/models/user.py\`:\*\*   
- Move \`User\` class   
- Move \`Role\` class   
- Move \`role\_assignments\` association table   
- Keep all user-related relationships intact   
   
\*\*2.2 Create \`app/models/blog.py\`:\*\*   
- Move \`BlogPost\` class   
- Include all blog-related fields and methods   
   
\*\*2.3 Create \`app/models/minecraft.py\`:\*\*   
- Move \`MinecraftCommand\` class   
- Move \`StringArray\` TypeDecorator (it's only used by MinecraftCommand)   
   
\*\*2.4 Create \`app/models/\_\_init\_\_.py\`:\*\*
\`\`\`python
\"\"\"Database models for flask-site application.\"\"\"
from app importdb
from.userimportUser,Role, role\_assignments
from.blogimportBlogPost
from.minecraftimportMinecraftCommand,StringArray   
\_\_all\_\_ =[
'User',
'Role',
'role\_assignments',
'BlogPost',
'MinecraftCommand',
'StringArray',
]
\`\`\`   
\*\*2.5 Delete old \`app/models.py\`\*\*   
### Phase 3: Migrate Routes to routes/ Directory (30 min)   
\*\*3.1 Move and rename route files:\*\*
\`\`\`bash   
# Move files withnewnames   
routes.py → app/routes/main.py
routes\_auth.py → app/routes/auth.py
routes\_blogpost.py → app/routes/blogpost.py
routes\_mc.py → app/routes/mc.py
routes\_admin.py → app/routes/admin.py
routes\_health.py → app/routes/health.py
routes\_profile.py → app/routes/profile.py
\`\`\`   
\*\*3.2 Update blueprint names in each route file\*\* (keep consistent):   
- \`main.py\`: Keep \`main\_bp\`   
- \`auth.py\`: Keep \`auth\_bp\` (was \`auth\`)   
- \`blogpost.py\`: Keep \`blogpost\_bp\`   
- \`mc.py\`: Keep \`mc\_bp\`   
- \`admin.py\`: Keep \`admin\_bp\`   
- \`health.py\`: Keep \`health\_bp\`   
- \`profile.py\`: Keep \`profile\_bp\`   
   
\*\*3.3 Create \`app/routes/\_\_init\_\_.py\`:\*\*
\`\`\`python
\"\"\"Route blueprints for flask-site application.\"\"\"
from.mainimportmain\_bp
from.authimportauth\_bp
from.blogpostimportblogpost\_bp
from.mcimportmc\_bp
from.adminimportadmin\_bp
from.healthimporthealth\_bp
from.profileimport profile\_bp   
\_\_all\_\_ =[
'main\_bp',
'auth\_bp',
'blogpost\_bp',
'mc\_bp',
'admin\_bp',
'health\_bp',
'profile\_bp',
]
\`\`\`   
### Phase 4: Update Import Statements (45 min)   
\*\*4.1 Update \`app/\_\_init\_\_.py\`:\*\*
\`\`\`python
from flask importFlask
from flask\_wtf importCSRFProtect
from flask\_sqlalchemy importSQLAlchemy
from flask\_login importLoginManager
from config importConfig
from.filtersimport register\_filters   
db =SQLAlchemy()
rcon =None
csrf =CSRFProtect()
login\_manager =LoginManager()   
# Versionfor health checks   
**version**  = "0.3.0"   
def create\_app():
app =Flask(\_\_name\_\_)
app.config.from\_object(Config)   
csrf.init\_app(app)
db.init\_app(app)
login\_manager.init\_app(app)   
register\_filters(app)   
# Register blueprints - cleaner imports   
from app.routesimport(
main\_bp,
auth\_bp,
blogpost\_bp,
mc\_bp,
admin\_bp,
health\_bp,
profile\_bp
)   
app.register\_blueprint(main\_bp)
app.register\_blueprint(auth\_bp)
app.register\_blueprint(blogpost\_bp)
app.register\_blueprint(mc\_bp)
app.register\_blueprint(admin\_bp)
app.register\_blueprint(health\_bp)
app.register\_blueprint(profile\_bp)   
app.rcon= rcon   
return app   
@login\_manager.user\_loader
def load\_user(user\_id):
from app.modelsimportUser
returnUser.query.get(int(user\_id))
\`\`\`   
\*\*4.2 Update all route files\*\* to use new model imports:
\`\`\`python   
# Old:   
from app.modelsimportUser,BlogPost,Role   
# New:   
from app.modelsimportUser,BlogPost,Role
\`\`\`   
\*\*4.3 Update \`app/forms.py\`\*\* if it imports models:
\`\`\`python   
# Should already work with:   
from app.modelsimportUser # etc.
\`\`\`   
\*\*4.4 Scan and update any test files\*\* in the codebase   
### Phase 5: Update Configuration (15 min)   
\*\*5.1 Add to \`config.py\`\*\* if needed:
\`\`\`python   
# Add profile upload folder if not present   
PROFILE\_UPLOAD\_FOLDER= os.path.join(os.getcwd(),'uploads/profiles')
\`\`\`   
\*\*5.2 Ensure upload directories exist:\*\*   
- Check that \`uploads/profiles/\` directory is created   
- Check that \`uploads/blog-posts/\` directory exists   
   
### Phase 6: Testing and Verification (30 min)   
\*\*6.1 Run the application:\*\*
\`\`\`bash
python run.py
\`\`\`   
\*\*6.2 Test critical paths:\*\*   
- ✅ Home page loads   
- ✅ Blog posts display   
- ✅ Login/logout works   
- ✅ Create new blog post   
- ✅ Admin dashboard (if logged in as admin)   
- ✅ Profile page loads   
- ✅ Health check endpoint: \`curl http://localhost:5000/health\`   
- ✅ Minecraft commands (if configured)   
   
\*\*6.3 Check for import errors:\*\*
\`\`\`bash   
# RunPython and try importing   
python -c \"from app import create\_app; app =create\_app()\"
\`\`\`   
\*\*6.4 Verify all blueprints registered:\*\*
\`\`\`bash
flask routes # IfFlaskCLI is configured
\`\`\`   
\*\*6.5 Check logs for warnings/errors\*\*   
## 🎯 Definition of Done   
- [ ] \`app/models/\` directory created with:   
- [ ] \`\_\_init\_\_.py\` (exports all models)   
- [ ] \`user.py\` (User, Role, role\_assignments)   
- [ ] \`blog.py\` (BlogPost)   
- [ ] \`minecraft.py\` (MinecraftCommand, StringArray)   
- [ ] \`app/routes/\` directory created with:   
- [ ] \`\_\_init\_\_.py\` (exports all blueprints)   
- [ ] \`main.py\` (main routes)   
- [ ] \`auth.py\` (authentication)   
- [ ] \`blogpost.py\` (blog CRUD)   
- [ ] \`mc.py\` (Minecraft)   
- [ ] \`admin.py\` (admin panel)   
- [ ] \`health.py\` (health checks)   
- [ ] \`profile.py\` (user profiles)   
- [ ] Old files deleted:   
- [ ] \`app/models.py\`   
- [ ] \`app/routes.py\`   
- [ ] \`app/routes\_\*.py\` (all 6 files)   
- [ ] \`app/\_\_init\_\_.py\` updated with clean imports   
- [ ] All route files use correct model imports   
- [ ] Application runs without import errors   
- [ ] All routes accessible and functional   
- [ ] Tests pass (if tests exist)   
- [ ] Health check endpoint returns 200 OK   
- [ ] Committed with proper Smart Commits format   
## 💡 Technical Considerations   
### Import Strategy (Industry Standard)   
Use the \*\*centralized \`\_\_init\_\_.py\` pattern\*\* for clean imports:   
\`\`\`python   
# In other files,import like this:   
from app.modelsimportUser,BlogPost,Role   
# NOT like this:   
from app.models.userimportUser
from app.models.blogimportBlogPost
\`\`\`   
This provides:   
- Single point of truth for exports   
- Easy to refactor later   
- Cleaner import statements   
- Follows Flask/SQLAlchemy conventions   
   
### Blueprint URL Prefixes   
Keep existing blueprint names unchanged to avoid breaking existing URL routes in templates:   
- \`main\_bp\` - No prefix (root \`/\`)   
- \`auth\_bp\` - Likely has \`/auth\` prefix or no prefix   
- \`blogpost\_bp\` - Routes like \`/post/\`   
- \`admin\_bp\` - \`/admin\`   
- \`profile\_bp\` - \`/profile\`   
- \`health\_bp\` - \`/health\`   
- \`mc\_bp\` - Minecraft routes   
   
\*\*Do NOT change blueprint variable names\*\* - this would break all \`url\_for()\` calls in templates!   
### Database Considerations   
- No database migration needed - only moving code   
- Model classes stay identical   
- Foreign keys and relationships preserved   
- Association tables maintained   
   
### Circular Import Prevention   
Current structure already handles this well:   
- Models imported in \`@login\_manager.user\_loader\` using lazy import   
- Routes import models after \`db\` is initialized   
- Continue this pattern in new structure   
   
## 🔍 Files to Scan   
Claude Code should scan these files for import updates:   
- \`app/\_\_init\_\_.py\` ⭐ (primary update)   
- \`app/routes/\*.py\` (all 7 route files)   
- \`app/forms.py\`   
- \`app/filters.py\`   
- \`run.py\`   
- Any files in \`tests/\` directory   
- Any migration scripts   
- \`config.py\` (verify upload folders)   
   
## ⚠️ Common Pitfalls to Avoid   
1. \*\*Don't change blueprint variable names\*\* - templates use them in \`url\_for()\`   
2. \*\*Preserve all model relationships\*\* - especially User↔Role many-to-many   
3. \*\*Keep \`StringArray\` with \`MinecraftCommand\`\*\* - it's only used there   
4. \*\*Don't forget \`\_\_all\_\_\`\*\* in \`\_\_init\_\_.py\` files for clean exports   
5. \*\*Test imports before committing\*\* - circular imports can be sneaky   
6. \*\*Verify health check works\*\* - it imports \`\_\_version\_\_\` from \`app\`   
   
## 📦 Expected Final Structure   
\`\`\`
app/
├── \_\_init\_\_.py # Updated imports
├── models/
│ ├── \_\_init\_\_.py # Export User, Role, BlogPost, MinecraftCommand
│ ├── user.py # User, Role, role\_assignments
│ ├── blog.py # BlogPost
│ └── minecraft.py # MinecraftCommand, StringArray
├── routes/
│ ├── \_\_init\_\_.py # Export all blueprints
│ ├── main.py # Main routes (formerly routes.py)
│ ├── auth.py # Auth routes (formerly routes\_auth.py)
│ ├── blogpost.py # Blog CRUD (formerly routes\_blogpost.py)
│ ├── mc.py # Minecraft (formerly routes\_mc.py)
│ ├── admin.py # Admin panel (formerly routes\_admin.py)
│ ├── health.py # Health checks (formerly routes\_health.py)
│ └── profile.py # User profiles (formerly routes\_profile.py)
├── utils/
│ ├── file\_validation.py
│ ├── image\_utils.py
│ └── pagination.py
├── forms.py
├── filters.py
├── templates/
└── static/
\`\`\`   
## ⏱️ Estimated Time Breakdown   
- \*\*Phase 1\*\* - Directory setup: 15 minutes   
- \*\*Phase 2\*\* - Split models: 45 minutes   
- \*\*Phase 3\*\* - Migrate routes: 30 minutes   
- \*\*Phase 4\*\* - Update imports: 45 minutes   
- \*\*Phase 5\*\* - Configuration: 15 minutes   
- \*\*Phase 6\*\* - Testing: 30 minutes   
   
\*\*Total: ~3 hours\*\*   
 --- 
   
