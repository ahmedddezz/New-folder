# Multi-User Access Control System - Explanation Guide

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Module Overview](#module-overview)
3. [Security Features](#security-features)
4. [Key Design Decisions](#key-design-decisions)
5. [Common Q&A](#common-qa)

---

## System Architecture

**Modular Design**: `CLI/Voice Input → Auth Module ↔ Users JSON → Session Manager → Command Dispatcher ↔ Admin Tools/Logger`

**Benefits**: Modularity, testability, maintainability, scalability

**Code Improvements**:
- Helper methods break complex functions into focused pieces
- Reduced nesting with early returns
- Code reuse via shared helper functions
- Linear flow with dictionary-based routing

---

## Module Overview

### 1. AuthModule (`auth.py`)
**Purpose**: Authentication and user management

**Key Features**:
- **User Storage**: JSON file (`users.json`) with `{username: {password_hash, role, locked}}`
- **Password Hashing**: SHA256 one-way hash (required by spec)
- **Authentication Flow**: Load users → Check existence → Check lock → Verify password hash → Handle failed attempts
- **Lockout System**: Two-level (in-memory counter + permanent JSON flag). Locks after 3 failed attempts.
- **Methods**: `add_user`, `remove_user`, `unlock_user`, `change_password`, `get_user_role`

### 2. SessionManager (`session.py`)
**Purpose**: Track active sessions with secure tokens

**Key Features**:
- **Tokens**: Cryptographically secure (`secrets.token_urlsafe(32)`)
- **Session Data**: `{username, role, created_at, last_activity}`
- **Storage**: In-memory dictionary (token → session data)
- **Methods**: `create_session`, `is_authenticated`, `is_admin`, `update_activity`, `end_session`, `_get_current_session()` helper

### 3. CommandDispatcher (`command_dispatcher.py`)
**Purpose**: Parse and route commands to handlers

**Key Features**:
- **Parsing**: Splits input → command + args (e.g., "add user john pass" → command="add user", args=["john", "pass"])
- **Normalization**: Maps "add user" → "add_user" (internal format) for voice/text compatibility
- **Routing**: Dictionary-based routing with permission checks
- **Handlers**: Each command has dedicated handler (`_handle_status`, `_handle_add_user`, etc.)
- **Helpers**: `_prompt_for_passwords()`, `_prompt_for_new_user()` for voice commands
- **Help Menu**: Role-based, shows commands with spaces for voice compatibility

### 4. VoiceIntegration (`voice.py`)
**Purpose**: Convert speech to commands

**Key Features**:
- **Recognition**: Google Speech Recognition API (requires internet)
- **Command Map**: Maps spoken variations to commands (e.g., "exit"/"quit" → "logout")
- **Mapping Algorithm**: Exact match → substring match → keyword match
- **Error Handling**: Detailed feedback for troubleshooting
- **Continuous Mode**: Stays active until "exit voice mode" is spoken
- **Exit Commands**: "exit voice mode", "exit voice", "leave voice mode", "stop voice", "back to text"

### 5. Logger (`logger.py`)
**Purpose**: Audit trail and debugging

**Key Features**:
- **Format**: `[Timestamp] [LEVEL] [username] message`
- **Levels**: LOGIN, COMMAND, ADMIN, ERROR
- **Storage**: Append-only `logs.txt`
- **CSV Export**: Parses logs into CSV with helper methods (`_read_log_lines`, `_parse_logs_to_csv`, `_parse_log_line`, `_write_csv_file`)
- **Methods**: `log_login_attempt`, `log_command`, `log_admin_action`, `log_error`, `view_logs`, `export_to_csv`

### 6. AdminTools (`admin.py`)
**Purpose**: Admin operations with validation and logging

**Key Features**:
- **Facade Pattern**: Wraps AuthModule and Logger
- **Validation**: Username ≥3 chars, password ≥4 chars
- **Safety**: Can't remove own account
- **Methods**: `add_user`, `remove_user`, `view_logs`, `export_logs`, `unlock_user` (all auto-logged)

### 7. Main System (`main.py`)
**Purpose**: Orchestrate modules and handle user interaction

**Key Flow**:
1. **Login Loop**: Prompt → authenticate → log attempt → create session
2. **Command Loop**: Get command (voice/text) → normalize → route → execute → display → repeat
3. **Voice Mode**: Type "voice" → continuous mode → say commands → say "exit voice mode" to exit
4. **Helpers**: `_show_welcome_message()`, `_get_user_command()`, `_handle_voice_command()`, `_handle_text_command()`, `_is_logout_command()`

---

## Security Features

1. **Password Security**: SHA256 hashing, no plaintext storage, secure input (`getpass`)
2. **Account Lockout**: 3-strike rule with two-level system (in-memory + permanent)
3. **Username Enumeration Prevention**: Generic error messages
4. **Session Security**: Cryptographically secure tokens, in-memory only
5. **Permission Checks**: RBAC with centralized admin checks
6. **Audit Trail**: Comprehensive logging with timestamps
7. **Input Validation**: Username/password length, role validation, command validation

---

## Key Design Decisions

1. **JSON Storage**: Simple, portable, sufficient for project scale
2. **In-Memory Sessions**: Fast, secure, but lost on restart (acceptable trade-off)
3. **Two-Level Lockout**: Balance between security and forgiveness
4. **Separate AdminTools**: Separation of concerns, centralized logging
5. **Command Dispatcher**: Single responsibility, extensible, consistent validation
6. **Voice Module**: Optional, isolated, testable, swappable
7. **User-Friendly Commands**: Spaces instead of underscores for voice recognition

---

## Common Q&A

**Q1: Why SHA256 not bcrypt?** Project spec requirement. Production would use bcrypt/Argon2.

**Q2: Why in-memory lockout?** Performance + forgiveness (resets on restart). Permanent lock in JSON provides security.

**Q3: Deleted users.json?** System recreates with default admin account.

**Q4: Can admins see passwords?** No. Passwords are hashed (one-way). Admins can only reset.

**Q5: Why Google Speech Recognition?** Free, accurate, simple. Alternative: offline engines like Vosk.

**Q6: No microphone?** System detects and falls back to text-only mode.

**Q7: Session invalidation?** Deleted on logout. Also lost on program restart (in-memory).

**Q8: Why log everything?** Security best practice: audit trail, debugging, accountability, forensics.

**Q9: Can users unlock themselves?** No. Only admins can unlock (prevents brute-force recovery).

**Q10: Locked vs lockout_state?** `locked` (JSON) = permanent, persists. `lockout_state` (memory) = temporary counter.

**Q11: Why confirmation for remove_user?** Destructive action (can't undo). Adding is reversible.

**Q12: Concurrent users?** Single-user implementation. Multi-user would need session DB, file locking.

**Q13: Code simplification?** Improved readability, maintainability, testability via helper methods and reduced nesting.

**Q14: Continuous voice mode?** Type "voice" → stays active → execute multiple commands → say "exit voice mode" to exit.

**Q15: Why spaces in commands?** Better voice recognition, user-friendly, consistent with help menu. Internal normalization handles conversion.

---

## Testing Scenarios

1. **Normal User**: Login → try admin command (denied) → status → logout
2. **Admin Flow**: Login → add user (typed) → add user (voice) → view logs → remove user → export logs
3. **Security**: Wrong password 3x → account locks → admin unlocks → user can login
4. **Voice Mode**: Type "voice" → say "status" → say "help" → say "add user" → say "exit voice mode"

---

## Code Quality Highlights

- Type hints throughout
- Comprehensive error handling with detailed messages
- Modular design (single responsibility)
- Complete documentation (docstrings)
- Consistent naming conventions
- Constants defined at class level
- Input validation on all user input
- Security-first design
- Simplified code structure (helper methods)
- Reduced duplication
- User-friendly commands (spaces for voice)
- Enhanced voice experience (continuous mode)
- Better debugging (detailed error messages)

---

## Presentation Tips

1. Start with architecture diagram
2. Demo live system
3. Emphasize security (hashing, lockout, logging)
4. Show code modularity
5. Use this guide for Q&A
6. Be honest if unsure

Good luck! 🎓
