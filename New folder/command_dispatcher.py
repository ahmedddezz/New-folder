"""
Command Dispatcher
Parses and dispatches commands to appropriate handlers.
"""
from typing import Optional, List, Tuple, Dict, Callable
from session import SessionManager
from auth import AuthModule
from admin import AdminTools
from logger import Logger


class CommandDispatcher:
    """Handles command parsing and dispatching."""
    
    def __init__(self, session_manager: SessionManager, auth_module: AuthModule, 
                 admin_tools: AdminTools, logger: Logger):
        """Initialize command dispatcher with dependencies."""
        self.session = session_manager
        self.auth = auth_module
        self.admin = admin_tools
        self.logger = logger
    
    def parse_command(self, command_input: str) -> Tuple[str, List[str]]:
        """
        Parse a command string into command and arguments.
        
        Args:
            command_input: Raw command string
        
        Returns:
            (command: str, args: List[str])
        """
        parts = command_input.strip().split()
        if not parts:
            return "", []
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        return command, args
    
    def execute_command(self, command: str, args: List[str]) -> Tuple[bool, str]:
        """Execute a command. Returns (success: bool, message: str)."""
        if not self.session.is_authenticated():
            return False, "You must be logged in to execute commands."
        
        username = self.session.get_current_user()
        self.session.update_activity()
        
        # Normalize and map command
        command = self._normalize_command(command)
        
        # Route to appropriate handler
        return self._route_command(command, args, username)
    
    def _normalize_command(self, command: str) -> str:
        """Normalize command name (handle voice commands and case)."""
        command = command.lower().strip()
        
        # Map multi-word voice commands to single-word commands
        voice_command_map = {
            "add user": "add_user",
            "remove user": "remove_user",
            "view logs": "view_logs",
            "change password": "change_password",
            "export logs": "export_logs",
            "exit voice mode": "exit voice mode"  # Keep as is for special handling
        }
        
        return voice_command_map.get(command, command)
    
    def _route_command(self, command: str, args: List[str], username: str) -> Tuple[bool, str]:
        """Route command to appropriate handler."""
        # Special command: exit voice mode (handled in main loop, not here)
        if command == "exit voice mode":
            return False, "This command should be handled by the main loop"
        
        # General commands (available to all users)
        if command == "help":
            return True, self._get_help_menu()
        elif command == "status":
            return self._handle_status(username)
        elif command == "logout":
            return self._handle_logout(username)
        elif command == "change_password":
            return self._handle_change_password(username, args)
        
        # Admin-only commands
        admin_commands: Dict[str, Callable] = {
            "add_user": self._handle_add_user,
            "remove_user": self._handle_remove_user,
            "view_logs": self._handle_view_logs,
            "export_logs": self._handle_export_logs
        }
        
        if command in admin_commands:
            if not self.session.is_admin():
                return False, "Permission denied: Admin access required."
            return admin_commands[command](username, args)
        
        # Unknown command
        self.logger.log_command(username, command, False)
        return False, f"Unknown command: {command}. Type 'help' for available commands."
    
    def _get_help_menu(self) -> str:
        """Generate help menu based on user role."""
        menu = "\n=== Available Commands ===\n\n"
        menu += "General Commands:\n"
        menu += "  status          - Show current session information\n"
        menu += "  logout          - Log out of the system\n"
        menu += "  help            - Show this help menu\n"
        menu += "  change password - Change your password\n"
        
        if self.session.is_admin():
            menu += "\nAdmin Commands:\n"
            menu += "  add user <username> <password> [role]  - Add a new user\n"
            menu += "  remove user <username>                 - Remove a user\n"
            menu += "  view logs [lines]                      - View system logs\n"
            menu += "  export logs                           - Export logs to CSV\n"
        
        menu += "\nVoice Commands:\n"
        menu += "  Type 'voice' to enter voice command mode\n"
        menu += "  Available voice commands: status, logout, help, change password\n"
        if self.session.is_admin():
            menu += "  Admin voice commands: add user, remove user, view logs, export logs\n"
        menu += "  Note: Voice recognition requires internet connection\n"
        menu += "\n"
        
        return menu
    
    def _handle_status(self, username: str) -> Tuple[bool, str]:
        """Handle status command."""
        session_info = self.session.get_session_info()
        if session_info:
            role = session_info["role"]
            created = session_info["created_at"]
            status_msg = f"Logged in as: {username}\n"
            status_msg += f"Role: {role}\n"
            status_msg += f"Session started: {created}"
            self.logger.log_command(username, "status", True)
            return True, status_msg
        return False, "Session information not available"
    
    def _handle_logout(self, username: str) -> Tuple[bool, str]:
        """Handle logout command."""
        self.logger.log_command(username, "logout", True)
        self.session.end_session()
        return True, "Logged out successfully"
    
    def _handle_change_password(self, username: str, args: List[str]) -> Tuple[bool, str]:
        """Handle change password command."""
        # Prompt for passwords if not provided (e.g., from voice command)
        if len(args) < 2:
            if len(args) == 0:
                args = self._prompt_for_passwords()
                if args is None:
                    return False, "Command cancelled"
            else:
                return False, "Usage: change password <old_password> <new_password>"
        
        old_password, new_password = args[0], args[1]
        
        if len(new_password) < 4:
            return False, "New password must be at least 4 characters"
        
        success, message = self.auth.change_password(username, old_password, new_password)
        self.logger.log_command(username, "change_password", success)
        return success, message
    
    def _prompt_for_passwords(self) -> Optional[List[str]]:
        """Prompt user for old and new passwords."""
        try:
            import getpass
            old_password = getpass.getpass("Enter current password: ")
            new_password = getpass.getpass("Enter new password: ")
            return [old_password, new_password]
        except (EOFError, KeyboardInterrupt):
            return None
    
    def _handle_add_user(self, username: str, args: List[str]) -> Tuple[bool, str]:
        """Handle add user command."""
        # Prompt for user details if not provided
        if len(args) < 2:
            if len(args) == 0:
                args = self._prompt_for_new_user()
                if args is None:
                    return False, "Command cancelled"
            else:
                return False, "Usage: add user <username> <password> [role]"
        
        new_username = args[0]
        new_password = args[1]
        role = args[2] if len(args) > 2 else "user"
        
        success, message = self.admin.add_user(new_username, new_password, role, username)
        return success, message
    
    def _prompt_for_new_user(self) -> Optional[List[str]]:
        """Prompt user for new user details."""
        try:
            new_username = input("Enter username: ").strip()
            import getpass
            new_password = getpass.getpass("Enter password: ")
            role_input = input("Enter role (user/admin, default: user): ").strip()
            role = role_input if role_input in ["admin", "user"] else "user"
            return [new_username, new_password, role]
        except (EOFError, KeyboardInterrupt):
            return None
    
    def _handle_remove_user(self, username: str, args: List[str]) -> Tuple[bool, str]:
        """Handle remove user command."""
        if len(args) < 1:
            return False, "Usage: remove user <username>"
        
        target_username = args[0]
        
        # Confirmation for safety
        print(f"Warning: You are about to remove user '{target_username}'.")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != 'yes':
            return False, "User removal cancelled"
        
        success, message = self.admin.remove_user(target_username, username)
        return success, message
    
    def _handle_view_logs(self, username: str, args: List[str]) -> Tuple[bool, str]:
        """Handle view logs command."""
        lines = None
        if args:
            try:
                lines = int(args[0])
            except ValueError:
                return False, "Invalid number of lines. Usage: view logs [lines]"
        
        logs = self.admin.view_logs(lines, username)
        return True, logs
    
    def _handle_export_logs(self, username: str) -> Tuple[bool, str]:
        """Handle export logs command."""
        success, message = self.admin.export_logs(username)
        return success, message

