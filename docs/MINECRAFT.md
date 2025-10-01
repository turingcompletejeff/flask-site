# Minecraft RCON Integration Documentation

Flask Portfolio Site - Minecraft Server Management Guide

## Table of Contents

- [Overview](#overview)
- [RCON Protocol](#rcon-protocol)
- [Setup and Configuration](#setup-and-configuration)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Command Storage](#command-storage)
- [Security Considerations](#security-considerations)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Minecraft integration provides remote server control via RCON (Remote Console) protocol, allowing authenticated users to execute server commands through a web interface.

**Key Features**:
- RCON connection management
- Command execution via web API
- Server query functionality
- Saved command presets
- Authentication-protected access
- CSRF exemption for external tools

**Library**: `mctools` (Python RCON client)

**Protocols**:
- RCON: Remote command execution
- Query: Server status and statistics

---

## RCON Protocol

### What is RCON?

RCON (Remote Console) is a protocol that allows remote administration of game servers, including Minecraft. It uses TCP and requires authentication.

**Default Port**: 25575 (configurable)

**Capabilities**:
- Execute server commands (e.g., `/time set day`, `/list`, `/tp`)
- Receive command output
- Persistent connection (reused across requests)

### Minecraft Server Configuration

**Enable RCON** in `server.properties`:
```properties
enable-rcon=true
rcon.port=25575
rcon.password=your_secure_password
```

**Security Notes**:
- Change default password immediately
- Restrict RCON port access (firewall)
- Use strong, unique passwords
- Consider VPN for remote access

---

## Setup and Configuration

### Environment Variables

**Required**:
```env
RCON_PASS=your_minecraft_rcon_password
MC_HOST=minecraft.server.com
MC_PORT=25575
```

**Configuration Mapping** (`config.py`):
```python
RCON_PASS = os.environ.get('RCON_PASS')
RCON_HOST = os.environ.get('MC_HOST')
RCON_PORT = os.environ.get('MC_PORT')
```

### Local Development

**Option 1: Local Minecraft Server**
```bash
# Download Minecraft server
wget https://launcher.mojang.com/v1/objects/.../server.jar

# Enable RCON in server.properties
enable-rcon=true
rcon.port=25575
rcon.password=dev_password

# Set environment variables
MC_HOST=localhost
MC_PORT=25575
RCON_PASS=dev_password
```

**Option 2: Remote Server**
```bash
# Point to existing Minecraft server
MC_HOST=mc.example.com
MC_PORT=25575
RCON_PASS=production_password
```

### Testing Connection

```python
from mctools import RCONClient

# Test RCON connection
rcon = RCONClient('localhost', port=25575)
if rcon.login('your_password'):
    response = rcon.command('help')
    print(response)
    rcon.stop()
else:
    print('RCON login failed')
```

---

## Architecture

### Connection Management

**Global RCON Object** (`app/__init__.py`):
```python
rcon = None  # Module-level variable

def create_app():
    app.rcon = rcon  # Attached to Flask app
```

**Connection Lifecycle**:
1. `rcon` initialized as `None`
2. First request calls `rconConnect()`
3. Connection established and authenticated
4. Connection reused for subsequent requests
5. Manually closed via `/mc/stop` or on error

### Blueprint Protection

**Blueprint-Level Authentication** (`routes_mc.py`):
```python
@mc_bp.before_request
def require_login():
    if not current_user.is_authenticated:
        flash("you must be logged in to access this page.", "warning")
        return redirect(url_for('auth.login'))
```

**Behavior**:
- All `/mc/*` routes require authentication
- Unauthenticated users redirected to login
- Prevents unauthorized server control

### CSRF Protection

**Exemption** (not currently implemented, but needed for `/mc/command`):

Current code does **not** exempt `/mc/command`, which may cause issues for external tools.

**Recommended Fix**:
```python
# In app/__init__.py
from app.routes_mc import mc_bp
csrf.exempt(mc_bp)  # Exempt entire blueprint

# OR exempt specific route
from flask_wtf import csrf
@csrf.exempt
@mc_bp.route('/mc/command', methods=['POST'])
def rconCommand():
    # ...
```

**Rationale**: External RCON tools cannot provide CSRF tokens.

---

## API Endpoints

### GET /mc

**Description**: Minecraft control panel page

**Authentication**: Required

**Response**: Rendered HTML template (`mc.html`)

**Usage**: Web interface for managing Minecraft server

---

### GET /mc/init

**Description**: Initialize RCON connection

**Authentication**: Required

**Response**:
- **Success**: Help command output (plain text)
- **Failure**: `"FAIL"` (plain text)

**Behavior**:
- Establishes RCON connection
- Authenticates with server
- Tests connection with `help` command
- Connection persists for future requests

**Example**:
```bash
curl -X GET http://localhost:8000/mc/init \
  --cookie "session=..."
```

**Response**:
```
Available commands:
/help - Shows this help
/list - Lists online players
...
```

---

### GET /mc/stop

**Description**: Stop RCON connection

**Authentication**: Required

**Response**: `"OK"` (plain text)

**Behavior**:
- Closes active RCON connection
- Resets global `rcon` variable to `None`
- Next command will re-establish connection

**Example**:
```bash
curl -X GET http://localhost:8000/mc/stop \
  --cookie "session=..."
```

---

### POST /mc/command

**Description**: Execute RCON command on Minecraft server

**Authentication**: Required

**CSRF Protection**: Should be exempt (not currently implemented)

**Request Body** (form-encoded):
```
command=list
```

**Response**:
- **Success**: Command output (plain text)
- **Failure**: `"FAIL"` (plain text)

**Command Format**:
- Commands submitted **without** leading `/`
- Example: `list` (not `/list`)
- RCON client handles command formatting

**Examples**:

1. **List Players**:
   ```bash
   curl -X POST http://localhost:8000/mc/command \
     --cookie "session=..." \
     -d "command=list"
   ```
   Response: `There are 3 of a max of 20 players online: Player1, Player2, Player3`

2. **Set Time**:
   ```bash
   curl -X POST http://localhost:8000/mc/command \
     --cookie "session=..." \
     -d "command=time set day"
   ```
   Response: `Set the time to 1000`

3. **Teleport Player**:
   ```bash
   curl -X POST http://localhost:8000/mc/command \
     --cookie "session=..." \
     -d "command=tp Steve 0 100 0"
   ```
   Response: `Teleported Steve to 0.0, 100.0, 0.0`

---

### GET /mc/query

**Description**: Query Minecraft server status via Query protocol

**Authentication**: Required

**Response**:
- **Success**: `200 OK` with JSON stats
- **Error**: `500 Internal Server Error` with error details

**Query Protocol**: Separate from RCON, provides server statistics

**Response Example**:
```json
{
  "hostname": "My Minecraft Server",
  "gametype": "SMP",
  "version": "1.20.1",
  "plugins": "CraftBukkit on Bukkit 1.20.1-R0.1-SNAPSHOT",
  "map": "world",
  "numplayers": 3,
  "maxplayers": 20,
  "hostport": 25565,
  "hostip": "192.168.1.100",
  "players": ["Player1", "Player2", "Player3"]
}
```

**Error Response**:
```json
{
  "error": "Connection closed",
  "message": "[Errno 111] Connection refused"
}
```

**Usage**:
```bash
curl -X GET http://localhost:8000/mc/query \
  --cookie "session=..."
```

---

### GET /mc/list

**Description**: List all saved Minecraft commands

**Authentication**: Required

**Response**: JSON array of command objects

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
    "command_name": "nighttime",
    "options": ["time set night"]
  },
  {
    "command_id": 3,
    "command_name": "teleport_spawn",
    "options": ["tp @p 0 100 0"]
  }
]
```

**Usage**:
```bash
curl -X GET http://localhost:8000/mc/list \
  --cookie "session=..."
```

---

## Command Storage

### MinecraftCommand Model

**Table**: `minecraft_commands`

**Schema**:
```python
class MinecraftCommand(db.Model):
    command_id = db.Column(db.Integer, primary_key=True)
    command_name = db.Column(db.String(20), nullable=True)
    options = db.Column(ARRAY(db.String(40)))  # PostgreSQL ARRAY
```

**Purpose**: Store frequently-used command presets

**Usage Example**:
```python
from app.models import MinecraftCommand

# Create command preset
cmd = MinecraftCommand(
    command_name='reset_world',
    options=[
        'time set day',
        'weather clear',
        'difficulty peaceful'
    ]
)
db.session.add(cmd)
db.session.commit()
```

**Retrieval**:
```python
# Get all commands
commands = MinecraftCommand.query.all()

# Convert to JSON
json_data = [cmd.to_dict() for cmd in commands]
```

**Note**: PostgreSQL-specific `ARRAY` type (not portable to MySQL/SQLite)

---

## Security Considerations

### Authentication

**Requirement**: All routes require authentication

**Protection Level**:
- Blueprint-level `@before_request` hook
- Redirects unauthenticated users to login
- Session-based authentication via Flask-Login

**Vulnerability**: No role-based access control (RBAC)
- Any authenticated user can execute commands
- Consider adding admin role requirement

**Recommended Improvement**:
```python
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Admin access required", "danger")
            return redirect(url_for('main_bp.index'))
        return f(*args, **kwargs)
    return decorated_function

@mc_bp.route('/mc/command', methods=['POST'])
@admin_required
def rconCommand():
    # ...
```

### CSRF Protection

**Current Status**: CSRF **enabled** for `/mc/command`

**Problem**: External tools cannot provide CSRF tokens

**Solution**: Exempt RCON routes from CSRF
```python
# In app/__init__.py
csrf.exempt(mc_bp)
```

**Trade-off**:
- Allows external tool integration
- Reduces CSRF attack protection
- Mitigated by authentication requirement

### Command Injection

**Risk**: Users can execute arbitrary Minecraft commands

**Current Protection**: None (trusted authenticated users)

**Attack Vector**:
```bash
# Malicious command
curl -X POST http://localhost:8000/mc/command \
  -d "command=op attacker"  # Grant attacker operator status
```

**Mitigation Options**:

1. **Command Whitelist**:
   ```python
   ALLOWED_COMMANDS = ['list', 'time', 'weather', 'tp', 'give']

   def is_safe_command(cmd):
       return cmd.split()[0] in ALLOWED_COMMANDS
   ```

2. **Command Validation**:
   ```python
   import re

   def validate_command(cmd):
       # Block dangerous commands
       if re.search(r'(op|deop|ban|pardon|stop)', cmd):
           raise ValueError('Command not allowed')
   ```

3. **Audit Logging**:
   ```python
   import logging

   logging.info(f"User {current_user.username} executed: {command}")
   ```

### Network Security

**Recommendations**:
- **Firewall**: Restrict RCON port (25575) to trusted IPs
- **VPN**: Use VPN for remote RCON access
- **Encryption**: RCON protocol is **not encrypted** (plaintext passwords!)
- **SSH Tunneling**: Tunnel RCON through SSH for encryption
  ```bash
  ssh -L 25575:localhost:25575 user@minecraft-server
  ```

### Password Security

**Environment Variables**: RCON password stored in `.env`

**Best Practices**:
- Use strong, unique passwords (20+ characters)
- Rotate passwords regularly
- Never commit `.env` to version control
- Use secrets management (Vault, AWS Secrets Manager)

---

## Usage Examples

### Web Interface

1. **Login**: Navigate to `/login` and authenticate
2. **Access Panel**: Go to `/mc`
3. **Execute Command**: Use web form to send commands

### Programmatic Access (Python)

```python
import requests

# Login to Flask app
session = requests.Session()
session.post('http://localhost:8000/login', data={
    'username': 'admin',
    'password': 'password'
})

# Initialize RCON connection
resp = session.get('http://localhost:8000/mc/init')
print(resp.text)  # Help output

# Execute command
resp = session.post('http://localhost:8000/mc/command', data={
    'command': 'list'
})
print(resp.text)  # Player list

# Get server stats
resp = session.get('http://localhost:8000/mc/query')
print(resp.json())  # Server statistics

# Stop connection
session.get('http://localhost:8000/mc/stop')
```

### Command-Line Access (curl)

```bash
# Login and save cookies
curl -X POST http://localhost:8000/login \
  -d "username=admin&password=password" \
  -c cookies.txt

# Initialize RCON
curl -X GET http://localhost:8000/mc/init \
  -b cookies.txt

# Execute command
curl -X POST http://localhost:8000/mc/command \
  -d "command=time set day" \
  -b cookies.txt

# Query server
curl -X GET http://localhost:8000/mc/query \
  -b cookies.txt

# Stop RCON
curl -X GET http://localhost:8000/mc/stop \
  -b cookies.txt
```

---

## Troubleshooting

### Problem: "FAIL" Response from Commands

**Causes**:
1. RCON not enabled on Minecraft server
2. Incorrect password
3. Server not reachable
4. Firewall blocking port 25575

**Debug Steps**:
```bash
# Test RCON connection manually
nc -zv minecraft-server 25575

# Check server.properties
grep rcon server.properties

# Verify environment variables
echo $RCON_PASS
echo $MC_HOST
echo $MC_PORT

# Test with Python
python3 -c "
from mctools import RCONClient
rcon = RCONClient('localhost', port=25575)
print(rcon.login('password'))
"
```

### Problem: Connection Timeout

**Cause**: Firewall blocking RCON port

**Solutions**:
```bash
# Open port in firewall (server-side)
sudo ufw allow 25575/tcp

# Check iptables
sudo iptables -L -n | grep 25575

# Test connectivity
telnet minecraft-server 25575
```

### Problem: Query Returns 500 Error

**Cause**: Query protocol not enabled

**Solution** (server.properties):
```properties
enable-query=true
query.port=25565
```

### Problem: CSRF Token Missing

**Cause**: CSRF protection enabled for `/mc/command`

**Solution**: Exempt blueprint from CSRF (see [Security Considerations](#csrf-protection))

### Problem: Connection Not Persisting

**Cause**: Global `rcon` variable reset

**Debug**:
```python
# Check connection status
from app import rcon
print(rcon)  # Should not be None after init

# Re-initialize if needed
curl http://localhost:8000/mc/init
```

---

## Performance Considerations

### Connection Pooling

**Current**: Single global RCON connection

**Limitation**: Not thread-safe for concurrent requests

**Potential Issues**:
- Multiple requests may conflict
- Connection state not synchronized

**Improvement** (for production):
```python
from threading import Lock

rcon_lock = Lock()

def rconCommand():
    with rcon_lock:
        if rconConnect():
            resp = rcon.command(request.form.get('command'))
            return resp
    return 'FAIL'
```

### Connection Timeout

**Current**: No explicit timeout configured

**Recommendation**:
```python
rcon = RCONClient(Config.RCON_HOST, port=Config.RCON_PORT, timeout=5)
```

---

## Future Enhancements

1. **Role-Based Access Control**: Restrict RCON to admin users
2. **Command Whitelist**: Limit allowed commands
3. **Audit Logging**: Track all executed commands
4. **WebSocket Support**: Real-time command output
5. **Connection Pooling**: Thread-safe connection management
6. **Encrypted Transport**: SSH tunneling for RCON
7. **Command History**: Store executed commands in database
8. **Scheduled Commands**: Cron-like command execution

---

## Code References

**RCON Routes**: `app/routes_mc.py:1-66`
**Global RCON Object**: `app/__init__.py:12`
**Blueprint Protection**: `app/routes_mc.py:12-16`
**Command Model**: `app/models.py:39-54`
**Configuration**: `config.py:13-15`

---

## External Resources

- [Minecraft RCON Protocol](https://wiki.vg/RCON)
- [mctools Library Documentation](https://pypi.org/project/mctools/)
- [Minecraft Server Properties](https://minecraft.fandom.com/wiki/Server.properties)
- [Minecraft Commands Reference](https://minecraft.fandom.com/wiki/Commands)

---

## Summary

The Minecraft RCON integration enables remote server management through a web interface. It uses the `mctools` library for RCON protocol communication and requires authentication for all operations. While functional, consider implementing command whitelisting, audit logging, and encrypted transport for production deployments.
