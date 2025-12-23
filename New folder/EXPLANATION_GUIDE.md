# Multi-User Access Control System - Explanation Guide

This document explains every detail of the system so you can confidently explain it to your professor.

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Module-by-Module Explanation](#module-by-module-explanation)
3. [Security Features](#security-features)
4. [Data Flow Examples](#data-flow-examples)
5. [Key Design Decisions](#key-design-decisions)
6. [Common Questions & Answers](#common-questions--answers)

---

## System Architecture Overview

The system follows a modular architecture with clear separation of concerns:

```
[CLI/Voice Input] 
    ↓
[Auth Module] ←→ [Users JSON file]
    ↓
[Session Manager] (in-memory tokens)
    ↓
[Command Dispatcher] ←→ [Admin Tools] ←→ [Logger]
    ↓                                    ↓
[Command Execution]              [Logs (file)]
```

### Why This Architecture?

1. **Modularity**: Each module has a single responsibility
2. **Testability**: Each component can be tested independently
3. **Maintainability**: Changes to one module don't break others
4. **Scalability**: Easy to add new features without rewriting existing code

---

## Module-by-Module Explanation

### 1. AuthModule (`auth.py`)

**Purpose**: Handles all authentication and user management.

#### Key Components:

**a) User Storage (`users.json`)**
- **Format**: JSON file with structure:
  ```json
  {
    "username": {
      "password_hash": "sha256_hash_here",
      "role": "admin" or "user",
      "locked": true/false
    }
  }
  ```
- **Why JSON?**: Human-readable, easy to parse, no database needed for this project
- **Persistence**: Data survives program restarts

**b) Password Hashing (`_hash_password`)**
- **Algorithm**: SHA256 (as required by project spec)
- **Process**:
  1. Takes plaintext password (e.g., "admin123")
  2. Converts to bytes using UTF-8 encoding
  3. Applies SHA256 hash algorithm
  4. Converts binary hash to hexadecimal string
- **Why Hash?**: Passwords are NEVER stored in plaintext - security requirement
- **Example**: "admin123" → "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
- **One-way**: Cannot reverse hash to get original password

**c) Authentication Flow (`authenticate` method)**
```
1. Load users from JSON file
2. Check if username exists
   → If not: return generic error (prevents username enumeration)
3. Check if account is locked (permanent lock in JSON)
   → If locked: return error
4. Check in-memory lockout state (failed attempts counter)
   → If >= 3: lock account permanently, return error
5. Hash the provided password
6. Compare hash with stored hash
   → If different: increment failed attempts, return error
   → If same: reset failed attempts, return success
```

**d) Lockout Mechanism**
- **Two-level system**:
  1. **In-memory lockout state**: Tracks failed attempts during current session
     - Stored in `self.lockout_state` dictionary
     - Resets on successful login
  2. **Permanent lock**: Stored in JSON file
     - Set when failed attempts >= 3
     - Requires admin to unlock
- **Why 3 attempts?**: Balance between security and usability
- **Why two levels?**: In-memory is fast, permanent lock persists across sessions

**e) User Management Methods**
- `add_user`: Creates new user, hashes password immediately
- `remove_user`: Deletes user from JSON, clears lockout state
- `unlock_user`: Resets locked flag and lockout counter
- `change_password`: Verifies old password, updates to new hash

---

### 2. SessionManager (`session.py`)

**Purpose**: Tracks active user sessions using tokens.

#### Key Concepts:

**a) Session Tokens**
- **Generation**: Uses `secrets.token_urlsafe(32)` - cryptographically secure random token
- **Format**: URL-safe base64 string (e.g., "xK9mP2qR7vT4wY8zA1bC3dE5fG6hI0j")
- **Why tokens?**: More secure than storing username directly, can be invalidated

**b) Session Data Structure**
```python
{
    "username": "admin",
    "role": "admin",
    "created_at": "2024-01-15T10:30:00",
    "last_activity": "2024-01-15T10:35:00"
}
```

**c) Current Session Tracking**
- `current_token`: Points to active session token
- `sessions`: Dictionary mapping token → session data
- **Why in-memory?**: Session tokens are temporary, don't need persistence

**d) Key Methods**
- `create_session`: Generates token, stores session data, sets as current
- `is_authenticated`: Checks if current_token exists and is valid
- `is_admin`: Quick check if current user has admin role
- `update_activity`: Updates last_activity timestamp (for future session timeout feature)
- `end_session`: Removes session data and clears current_token

---

### 3. CommandDispatcher (`command_dispatcher.py`)

**Purpose**: Parses user input and routes commands to appropriate handlers.

#### Command Processing Flow:

```
User Input → parse_command() → execute_command() → Handler Method → Response
```

**a) Command Parsing (`parse_command`)**
- Splits input by spaces
- First word = command
- Remaining words = arguments
- Example: "add_user john password123 user" → command="add_user", args=["john", "password123", "user"]

**b) Command Normalization**
- Handles voice commands that come as multi-word strings
- "add user" → "add_user"
- "view logs" → "view_logs"
- This allows both typed and voice commands to work the same way

**c) Permission Checking**
- Before executing admin commands, checks `session.is_admin()`
- Returns clear error: "Permission denied: Admin access required."
- **Why check here?**: Centralized security - can't forget to check permissions

**d) Command Handlers**
Each command has a dedicated handler method:
- `_handle_status`: Shows current session info
- `_handle_logout`: Logs command, ends session
- `_handle_add_user`: Validates args, calls admin.add_user()
- `_handle_remove_user`: Requires confirmation (safety feature)
- `_handle_view_logs`: Supports optional line limit parameter
- `_handle_change_password`: Validates password length

**e) Help Menu (`_get_help_menu`)**
- Dynamically generated based on user role
- Shows only commands available to current user
- Clear formatting for readability

**f) Voice Command Support**
- Commands without arguments can be called via voice
- Commands with arguments prompt user for input when called via voice
- Example: Voice says "add user" → system prompts for username, password, role

---

### 4. VoiceIntegration (`voice.py`)

**Purpose**: Converts speech to text and maps to commands.

#### How It Works:

**a) Speech Recognition Setup**
- Uses `speech_recognition` library (wrapper for Google Speech Recognition API)
- Initializes `Recognizer` and `Microphone` objects
- Calibrates microphone for ambient noise (reduces false positives)

**b) Command Mapping (`COMMAND_MAP`)**
```python
{
    "status": ["status", "state", "info", "information"],
    "logout": ["logout", "log out", "exit", "quit"],
    "add user": ["add user", "create user", "new user"],
    ...
}
```
- Maps canonical command names to multiple spoken variations
- Allows natural language (e.g., "exit" or "quit" both map to "logout")

**c) Recognition Process (`listen_for_command`)**
```
1. Listen to microphone (5 second timeout)
2. Convert audio to text using Google Speech Recognition
3. Convert text to lowercase
4. Map spoken text to command using _map_to_command()
5. Return command string or None if not recognized
```

**d) Mapping Algorithm (`_map_to_command`)**
- **Step 1**: Direct match - check if command name is in spoken text
- **Step 2**: Keyword match - check if any keyword is in spoken text
- Returns first match found
- Returns None if no match (falls back to text mode)

**e) Error Handling**
- `UnknownValueError`: Couldn't understand audio → returns None
- `RequestError`: API error → returns None
- `WaitTimeoutError`: No input detected → returns None
- All errors handled gracefully, system continues in text mode

---

### 5. Logger (`logger.py`)

**Purpose**: Records all system events for auditing and debugging.

#### Log Structure:

**a) Log Format**
```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [username] message
```
- **Timestamp**: ISO format for easy parsing
- **Level**: LOGIN, COMMAND, ADMIN, ERROR
- **Username**: Optional (None for system events)
- **Message**: Human-readable description

**b) Log Types**
- `log_login_attempt`: Records every login attempt (success/failure)
- `log_command`: Records every command execution
- `log_admin_action`: Special logging for admin operations
- `log_error`: Records system errors

**c) Log File Management**
- File: `logs.txt` (plain text, append-only)
- Created automatically if doesn't exist
- Appends new entries (never overwrites)

**d) View Logs (`view_logs`)**
- Can view all logs or last N lines
- Useful for admins to audit system activity
- Returns formatted string for display

**e) CSV Export (`export_to_csv`)**
- Parses log file line by line
- Extracts timestamp, level, username, message
- Writes to `logs.csv` with headers
- Handles malformed lines gracefully (skips them)

**f) Why Logging?**
- **Security**: Track who did what and when
- **Debugging**: Find issues in production
- **Compliance**: Audit trail for sensitive operations
- **Accountability**: Users know their actions are logged

---

### 6. AdminTools (`admin.py`)

**Purpose**: Implements admin-specific operations with proper logging.

#### Design Pattern: Facade

This module acts as a facade over `AuthModule` and `Logger`:
- Provides admin-specific interface
- Adds validation (username length, password length)
- Adds safety checks (can't remove own account)
- Automatically logs all admin actions

#### Key Methods:

**a) `add_user`**
- Validates input (username >= 3 chars, password >= 4 chars)
- Calls `auth.add_user()` to actually create user
- Logs admin action and command execution
- Returns success/failure with message

**b) `remove_user`**
- Safety check: Prevents admin from removing their own account
- Calls `auth.remove_user()` to delete user
- Logs the action
- **Note**: Confirmation is handled in CommandDispatcher (not here)

**c) `view_logs`**
- Wrapper around `logger.view_logs()`
- Logs that admin viewed logs (meta-logging)
- Supports optional line limit

**d) `export_logs`**
- Calls `logger.export_to_csv()`
- Logs both the command and admin action
- Returns success/failure message

**e) `unlock_user`**
- Calls `auth.unlock_user()` to reset lock
- Logs the unlock action
- Useful for recovering locked accounts

---

### 7. Main System (`main.py`)

**Purpose**: Orchestrates all modules and handles user interaction.

#### System Initialization:

```python
self.auth = AuthModule()           # User storage & authentication
self.session = SessionManager()     # Session tracking
self.logger = Logger()              # Logging system
self.admin = AdminTools(...)        # Admin operations
self.dispatcher = CommandDispatcher(...)  # Command routing
self.voice = VoiceIntegration()     # Voice recognition
```

**Dependency Injection**: Each module receives its dependencies through constructor
- Makes testing easier
- Makes dependencies explicit
- Allows swapping implementations

#### Main Flow:

**a) Login Loop**
```
1. Prompt for username and password
2. Call auth.authenticate()
3. Log login attempt (success or failure)
4. If successful:
   - Get user role
   - Create session token
   - Welcome user
5. If failed:
   - Show error message
   - Ask if user wants to retry
```

**b) Command Loop**
```
1. Check if voice_mode is active
2. If voice_mode:
   - Listen for voice command
   - Map to command string
   - Set args = [] (will prompt if needed)
3. If text_mode:
   - Read user input
   - Check for "voice" command
   - Parse command and arguments
4. Execute command via dispatcher
5. Display result
6. If logout: break loop
7. If voice_mode: return to text_mode
```

**c) Error Handling**
- `KeyboardInterrupt` (Ctrl+C): Graceful handling, doesn't crash
- `EOFError`: End of input, exit gracefully
- General exceptions: Log error, display message, continue running

**d) Voice Mode**
- Activated by typing "voice" command
- Listens for commands continuously
- Falls back to text mode if recognition fails
- Returns to text mode after each command (for commands needing arguments)

---

## Security Features

### 1. Password Security
- **Hashing**: SHA256 one-way hash (cannot be reversed)
- **No Plaintext Storage**: Passwords never stored as-is
- **Secure Input**: Uses `getpass` module (hides password while typing)

### 2. Account Lockout
- **3-Strike Rule**: Locks after 3 failed attempts
- **Two-Level System**: In-memory counter + permanent lock flag
- **Prevents Brute Force**: Attackers can't try unlimited passwords

### 3. Username Enumeration Prevention
- **Generic Error Messages**: "Invalid username or password" for both wrong username and wrong password
- **Timing**: Response time is similar for both cases (no timing attacks)

### 4. Session Security
- **Cryptographically Secure Tokens**: Uses `secrets` module (not predictable)
- **In-Memory Only**: Tokens not stored on disk
- **Automatic Cleanup**: Sessions cleared on logout

### 5. Permission Checks
- **Role-Based Access Control (RBAC)**: Admin vs User roles
- **Centralized Checks**: All admin commands check permissions
- **Clear Error Messages**: Users know why access was denied

### 6. Audit Trail
- **Comprehensive Logging**: All actions logged with username and timestamp
- **Immutable Logs**: Append-only log file
- **Admin Visibility**: Admins can view all logs

### 7. Input Validation
- **Username Length**: Minimum 3 characters
- **Password Length**: Minimum 4 characters
- **Role Validation**: Only "admin" or "user" allowed
- **Command Validation**: Unknown commands rejected

---

## Data Flow Examples

### Example 1: User Login

```
1. User types username and password
2. main.py → auth.authenticate(username, password)
3. auth.py:
   - Loads users.json
   - Checks if username exists
   - Checks if account locked
   - Hashes provided password
   - Compares hashes
   - Returns (True, "Login successful")
4. main.py → logger.log_login_attempt(username, True)
5. main.py → session.create_session(username, role)
6. session.py:
   - Generates secure token
   - Stores session data
   - Sets current_token
7. User is now logged in
```

### Example 2: Admin Adds User (Typed Command)

```
1. User types: "add_user john password123 user"
2. main.py → dispatcher.parse_command(input)
   - Returns: ("add_user", ["john", "password123", "user"])
3. main.py → dispatcher.execute_command("add_user", args)
4. dispatcher.py:
   - Checks session.is_admin() → True
   - Calls _handle_add_user(username, args)
5. _handle_add_user:
   - Extracts: username="john", password="password123", role="user"
   - Calls admin.add_user("john", "password123", "user", current_user)
6. admin.py:
   - Validates username length (>= 3) ✓
   - Validates password length (>= 4) ✓
   - Calls auth.add_user("john", "password123", "user")
7. auth.py:
   - Checks if "john" exists → No
   - Hashes password: _hash_password("password123")
   - Creates user entry in users dictionary
   - Saves to users.json
   - Returns (True, "User 'john' added successfully")
8. admin.py:
   - Logs admin action: logger.log_admin_action(...)
   - Logs command: logger.log_command(...)
   - Returns (True, "User 'john' added successfully")
9. dispatcher.py returns success message
10. main.py displays message to user
```

### Example 3: Voice Command "Status"

```
1. User types "voice" to enter voice mode
2. main.py sets voice_mode = True
3. User speaks: "status"
4. main.py → voice.listen_for_command()
5. voice.py:
   - Listens to microphone
   - Converts audio to text: "status"
   - Calls _map_to_command("status")
   - Finds match in COMMAND_MAP → returns "status"
6. main.py receives command = "status", args = []
7. main.py → dispatcher.execute_command("status", [])
8. dispatcher.py:
   - Normalizes command (already "status")
   - Calls _handle_status(username)
9. _handle_status:
   - Gets session info from session manager
   - Formats status message
   - Logs command execution
   - Returns status message
10. main.py displays status
11. Voice mode returns to text mode
```

### Example 4: Failed Login (Lockout)

```
1. User enters wrong password 3 times
2. Attempt 1:
   - auth.authenticate() → False
   - lockout_state["user"] = 1
   - Returns: "Invalid password. 2 attempt(s) remaining."
3. Attempt 2:
   - lockout_state["user"] = 2
   - Returns: "Invalid password. 1 attempt(s) remaining."
4. Attempt 3:
   - lockout_state["user"] = 3
   - user["locked"] = True (saved to JSON)
   - Returns: "Account locked due to too many failed login attempts."
5. Attempt 4:
   - Checks user["locked"] → True
   - Returns: "Account is locked. Please contact an administrator."
```

---

## Key Design Decisions

### 1. Why JSON for User Storage?
- **Simplicity**: No database setup required
- **Portability**: Easy to backup/restore
- **Readability**: Can inspect/edit manually if needed
- **Sufficient**: For this project scale, JSON is adequate

### 2. Why In-Memory Session Tokens?
- **Performance**: Fast lookups
- **Security**: Tokens not persisted (more secure)
- **Simplicity**: No need for session database
- **Trade-off**: Sessions lost on program restart (acceptable for this project)

### 3. Why Two-Level Lockout?
- **In-memory**: Fast, resets on restart (forgiveness)
- **Permanent**: Persists across sessions (security)
- **Balance**: Prevents brute force while allowing recovery

### 4. Why Separate AdminTools Module?
- **Separation of Concerns**: Auth handles storage, Admin handles business logic
- **Logging**: Centralized admin action logging
- **Validation**: Admin-specific validation rules
- **Future-Proof**: Easy to add more admin features

### 5. Why Command Dispatcher Pattern?
- **Single Responsibility**: One place handles all command routing
- **Extensibility**: Easy to add new commands
- **Consistency**: All commands go through same validation/permission checks
- **Maintainability**: Command logic centralized

### 6. Why Voice Integration as Separate Module?
- **Optional Feature**: System works without voice
- **Isolation**: Voice errors don't crash main system
- **Testability**: Can test voice separately
- **Future**: Easy to swap voice recognition engines

---

## Common Questions & Answers

### Q1: Why SHA256 and not bcrypt or Argon2?
**A**: Project specification requires SHA256. In production, bcrypt/Argon2 would be better (they're slower, making brute force harder), but for this academic project, SHA256 meets requirements.

### Q2: Why store lockout state in memory?
**A**: Two reasons:
1. Performance - faster than file I/O
2. Forgiveness - resets on restart (user can try again after program restart)

The permanent lock in JSON provides the security (prevents persistent attacks).

### Q3: What happens if users.json is deleted?
**A**: System recreates it with default admin account. This is a safety feature for first-time setup.

### Q4: Can users see other users' passwords?
**A**: No. Passwords are hashed. Even admins can't see original passwords. They can only reset them.

### Q5: Why use Google Speech Recognition?
**A**: It's free, accurate, and works offline after initial setup. Alternative: could use offline engines like Vosk, but Google is simpler for this project.

### Q6: What if microphone isn't available?
**A**: System detects this and falls back to text-only mode. Voice is optional feature.

### Q7: How are sessions invalidated?
**A**: On logout, session data is deleted and current_token is cleared. Sessions are also lost on program restart (in-memory only).

### Q8: Why log everything?
**A**: Security best practice:
- Audit trail for compliance
- Debugging when issues occur
- Accountability (users know actions are logged)
- Forensics (investigate security incidents)

### Q9: Can a user unlock their own account?
**A**: No. Only admins can unlock accounts. This prevents users from brute-forcing their way back in.

### Q10: What's the difference between "locked" and lockout_state?
**A**: 
- `locked` (in JSON): Permanent lock, persists across sessions, requires admin unlock
- `lockout_state` (in memory): Temporary counter, resets on successful login or program restart

### Q11: Why confirmation for remove_user but not add_user?
**A**: Removing a user is destructive (can't undo). Adding a user is reversible (can be removed). Confirmation prevents accidental deletions.

### Q12: How does the system handle concurrent users?
**A**: This implementation is single-user (one session at a time). For multi-user, would need:
- Session database instead of in-memory
- File locking for users.json
- More sophisticated token management

---

## Testing Scenarios to Demonstrate

### Scenario 1: Normal User Flow
1. Login as normal user
2. Try to run admin command → Permission denied
3. Run status command → Shows user info
4. Logout

### Scenario 2: Admin Flow
1. Login as admin
2. Add user via typed command
3. Add user via voice command
4. View logs
5. Remove user (with confirmation)
6. Export logs to CSV

### Scenario 3: Security Features
1. Try wrong password 3 times → Account locks
2. Try to login again → Account locked message
3. Login as admin
4. Unlock the locked account
5. User can login again

### Scenario 4: Voice Commands
1. Type "voice" to enter voice mode
2. Say "status" → Shows status
3. Say "help" → Shows help menu
4. Say "add user" → Prompts for details
5. Complete user creation

---

## Code Quality Points to Mention

1. **Type Hints**: All functions have type hints for clarity
2. **Error Handling**: Try-except blocks prevent crashes
3. **Modularity**: Each module has single responsibility
4. **Documentation**: Docstrings explain purpose and parameters
5. **Consistent Naming**: Clear, descriptive variable/function names
6. **No Hardcoded Values**: Constants defined at class level
7. **Input Validation**: All user input validated before processing
8. **Security First**: Security considerations in every design decision

---

## Presentation Tips

1. **Start with Architecture**: Show the diagram, explain flow
2. **Demo Live**: Run the system, show it working
3. **Explain Security**: Emphasize password hashing, lockout, logging
4. **Show Code Structure**: Point out modularity, separation of concerns
5. **Handle Questions**: Use this guide to answer any questions
6. **Be Honest**: If you don't know something, say you'll look into it

Good luck with your presentation! 🎓

