# Multi-User Access Control System

A terminal control panel supporting multiple users (admin & normal users) with authentication, command execution via keyboard or voice, and comprehensive logging.

## Features

### Core Features
- ✅ Persistent user store (JSON file) with username, hashed password (SHA256), and role
- ✅ Login with username + password
- ✅ Command parser for typed commands (status, logout, help)
- ✅ Voice command mapping to the same commands
- ✅ Admin commands: add_user, remove_user, view_logs
- ✅ Logging of commands and login attempts
- ✅ Lock user after 3 failed logins
- ✅ Clear help menu and permission error messages

### Advanced Features
- ✅ Password change functionality
- ✅ Export logs to CSV
- ✅ Voice-only mode
- ✅ Simple session tokens in memory (to track current user)

## Architecture

```
[CLI/Voice] → [Auth Module] → [Session Manager] → [Command Dispatcher]
                    |                                      |
                    v                                      v
            [Users JSON]                            [Logs (file)]
```

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

**Note:** On some systems, you may need to install PyAudio separately:
- **Windows:** `pip install pipwin && pipwin install pyaudio`
- **Linux:** `sudo apt-get install portaudio19-dev python3-pyaudio`
- **macOS:** `brew install portaudio && pip install pyaudio`

## Usage

### Starting the System

```bash
python main.py
```

### Default Admin Account

- **Username:** `admin`
- **Password:** `admin123`

**⚠️ Important:** Change the default password after first login!

### Login

The system will prompt for username and password. After successful login, you can enter commands.

### Available Commands

#### General Commands (All Users)
- `status` - Show current session information
- `logout` - Log out of the system
- `help` - Show help menu
- `change_password <old_password> <new_password>` - Change your password

#### Admin Commands
- `add_user <username> <password> [role]` - Add a new user (role: admin or user)
- `remove_user <username>` - Remove a user (requires confirmation)
- `view_logs [lines]` - View system logs (optional: number of recent lines)
- `export_logs` - Export logs to CSV file

#### Voice Commands
- Type `voice` to enter voice-only mode
- Speak any of the available commands
- The system will recognize and execute the command

### Voice Command Examples

You can say:
- "status" or "state" or "info"
- "logout" or "exit" or "quit"
- "help" or "commands"
- "add user" followed by username and password
- "remove user" followed by username
- "view logs" or "show logs"
- "change password"
- "export logs"

## Security Features

1. **Password Hashing:** All passwords are hashed using SHA256 before storage
2. **Account Lockout:** Accounts are locked after 3 failed login attempts
3. **Role-Based Access:** Admin commands require admin privileges
4. **Session Management:** User sessions are tracked with secure tokens
5. **Command Logging:** All commands and login attempts are logged

## File Structure

```
.
├── main.py                 # Main entry point
├── auth.py                 # Authentication module
├── session.py              # Session manager
├── command_dispatcher.py   # Command parser and dispatcher
├── voice.py                # Voice integration
├── logger.py               # Logging functionality
├── admin.py                # Admin tools
├── users.json              # User database (created automatically)
├── logs.txt                # System logs (created automatically)
├── logs.csv                # Exported logs (created on export)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Demo Checklist

✅ Admin logs in and adds a new user via typed command  
✅ Admin adds a new user via voice command  
✅ Non-admin logs in and runs status command  
✅ Invalid logins increment lockout counter  
✅ Logs contain login attempts and command invocations  

## Example Session

```
==================================================
Multi-User Access Control System
==================================================

=== Login ===
Username: admin
Password: ******

Login successful
Welcome, admin! (Role: admin)

Type 'help' for available commands.
Type 'voice' to enter voice command mode.
Type 'logout' to exit.

admin> help

=== Available Commands ===

General Commands:
  status          - Show current session information
  logout          - Log out of the system
  help            - Show this help menu
  change_password - Change your password

Admin Commands:
  add_user <username> <password> [role]  - Add a new user
  remove_user <username>                 - Remove a user
  view_logs [lines]                      - View system logs
  export_logs                           - Export logs to CSV

admin> add_user john password123 user
User 'john' added successfully

admin> logout
Logged out successfully

Session ended. Goodbye!
```

## Troubleshooting

### Voice Recognition Issues

If voice commands don't work:
1. Ensure your microphone is connected and working
2. Check that PyAudio is properly installed
3. Try speaking clearly and in a quiet environment
4. The system will fall back to text mode if voice recognition fails

### Account Locked

If your account is locked:
1. Contact an administrator to unlock your account
2. Admins can unlock accounts using the unlock functionality (can be added to admin commands)

## Development

### Module Responsibilities

- **auth.py:** User storage, password hashing, authentication, lockout
- **session.py:** Session token management, current user tracking
- **command_dispatcher.py:** Command parsing, routing, help menu
- **voice.py:** Speech recognition, command mapping
- **logger.py:** Logging, log viewing, CSV export
- **admin.py:** Admin-specific operations
- **main.py:** System integration and main loop

## License

This project is for educational purposes.

