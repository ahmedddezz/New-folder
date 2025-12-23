"""
Command Dispatcher
Parses and dispatches commands to appropriate handlers.
"""
from typing import Optional, List, Tuple
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
        """
        Execute a command.
        
        Returns:
            (success: bool, message: str)
        """
        if not self.session.is_authenticated():
            return False, "You must be logged in to execute commands."
        
        username = self.session.get_current_user()
        self.session.update_activity()
        
        # Normalize command (handle voice commands)
        command = command.lower().strip()
        
        # Handle multi-word commands from voice
        if command == "add user":
            command = "add_user"
        elif command == "remove user":
            command = "remove_user"
        elif command == "view logs":
            command = "view_logs"
        elif command == "change password":
            command = "change_password"
        elif command == "export logs":
            command = "export_logs"
        
        # Dispatch commands
        if command == "help":
            return True, self._get_help_menu()
        
        elif command == "status":
            return self._handle_status(username)
        
        elif command == "logout":
            return self._handle_logout(username)
        
        elif command == "change_password":
            return self._handle_change_password(username, args)
        
        # Admin commands
        elif command == "add_user":
            if not self.session.is_admin():
                return False, "Permission denied: Admin access required."
            return self._handle_add_user(username, args)
        
        elif command == "remove_user":
            if not self.session.is_admin():
                return False, "Permission denied: Admin access required."
            return self._handle_remove_user(username, args)
        
        elif command == "view_logs":
            if not self.session.is_admin():
                return False, "Permission denied: Admin access required."
            return self._handle_view_logs(username, args)
        
        elif command == "export_logs":
            if not self.session.is_admin():
                return False, "Permission denied: Admin access required."
            return self._handle_export_logs(username)
        
        else:
            self.logger.log_command(username, command, False)
            return False, f"Unknown command: {command}. Type 'help' for available commands."
    
    def _get_help_menu(self) -> str:
        """Generate help menu based on user role."""
        menu = "\n=== Available Commands ===\n\n"
        menu += "General Commands:\n"
        menu += "  status          - Show current session information\n"
        menu += "  logout          - Log out of the system\n"
        menu += "  help            - Show this help menu\n"
        menu += "  change_password - Change your password\n"
        
        if self.session.is_admin():
            menu += "\nAdmin Commands:\n"
            menu += "  add_user <username> <password> [role]  - Add a new user\n"
            menu += "  remove_user <username>                 - Remove a user\n"
            menu += "  view_logs [lines]                      - View system logs\n"
            menu += "  export_logs                           - Export logs to CSV\n"
        
        menu += "\nVoice Commands:\n"
        menu += "  All typed commands can also be issued via voice\n"
        menu += "  Use 'voice' command to enter voice-only mode\n"
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
        if len(args) < 2:
            # If called via voice or without args, prompt for them
            if len(args) == 0:
                try:
                    import getpass
                    old_password = getpass.getpass("Enter current password: ")
                    new_password = getpass.getpass("Enter new password: ")
                    args = [old_password, new_password]
                except (EOFError, KeyboardInterrupt):
                    return False, "Command cancelled"
            else:
                return False, "Usage: change_password <old_password> <new_password>"
        
        old_password = args[0]
        new_password = args[1]
        
        if len(new_password) < 4:
            return False, "New password must be at least 4 characters"
        
        success, message = self.auth.change_password(username, old_password, new_password)
        self.logger.log_command(username, "change_password", success)
        return success, message
    
    def _handle_add_user(self, username: str, args: List[str]) -> Tuple[bool, str]:
        """Handle add_user command."""
        if len(args) < 2:
            # If called via voice or without args, prompt for them
            if len(args) == 0:
                try:
                    new_username = input("Enter username: ").strip()
                    import getpass
                    new_password = getpass.getpass("Enter password: ")
                    role_input = input("Enter role (user/admin, default: user): ").strip()
                    role = role_input if role_input in ["admin", "user"] else "user"
                    args = [new_username, new_password, role]
                except (EOFError, KeyboardInterrupt):
                    return False, "Command cancelled"
            else:
                return False, "Usage: add_user <username> <password> [role]"
        
        new_username = args[0]
        new_password = args[1]
        role = args[2] if len(args) > 2 else "user"
        
        success, message = self.admin.add_user(new_username, new_password, role, username)
        return success, message
    
    def _handle_remove_user(self, username: str, args: List[str]) -> Tuple[bool, str]:
        """Handle remove_user command."""
        if len(args) < 1:
            return False, "Usage: remove_user <username>"
        
        target_username = args[0]
        
        # Confirmation for safety
        print(f"Warning: You are about to remove user '{target_username}'.")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != 'yes':
            return False, "User removal cancelled"
        
        success, message = self.admin.remove_user(target_username, username)
        return success, message
    
    def _handle_view_logs(self, username: str, args: List[str]) -> Tuple[bool, str]:
        """Handle view_logs command."""
        lines = None
        if args:
            try:
                lines = int(args[0])
            except ValueError:
                return False, "Invalid number of lines. Usage: view_logs [lines]"
        
        logs = self.admin.view_logs(lines, username)
        return True, logs
    
    def _handle_export_logs(self, username: str) -> Tuple[bool, str]:
        """Handle export_logs command."""
        success, message = self.admin.export_logs(username)
        return success, message

