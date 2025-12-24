"""
Admin Tools Module
Implements admin-specific commands and functionality.
"""
from typing import Optional
from auth import AuthModule
from logger import Logger


class AdminTools:
    """Handles admin-specific operations."""
    
    def __init__(self, auth_module: AuthModule, logger: Logger):
        """Initialize admin tools with dependencies."""
        self.auth = auth_module
        self.logger = logger
    
    def add_user(self, username: str, password: str, role: str = "user", current_user: str = "") -> tuple[bool, str]:
        """Add a new user (admin only). Returns (success: bool, message: str)."""
        # Validate input
        if not username or not password:
            return False, "Username and password are required"
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        if len(password) < 4:
            return False, "Password must be at least 4 characters"
        
        # Add user
        success, message = self.auth.add_user(username, password, role)
        
        # Log action if successful
        if success:
            self.logger.log_admin_action(current_user, "add_user", username)
            self.logger.log_command(current_user, f"add_user {username}", True)
        
        return success, message
    
    def remove_user(self, username: str, current_user: str = "") -> tuple[bool, str]:
        """Remove a user (admin only). Returns (success: bool, message: str)."""
        if not username:
            return False, "Username is required"
        if username == current_user:
            return False, "Cannot remove your own account"
        
        success, message = self.auth.remove_user(username)
        
        if success:
            self.logger.log_admin_action(current_user, "remove_user", username)
            self.logger.log_command(current_user, f"remove_user {username}", True)
        
        return success, message
    
    def view_logs(self, lines: Optional[int] = None, current_user: str = "") -> str:
        """View system logs (admin only). Returns log content as string."""
        self.logger.log_command(current_user, "view_logs", True)
        return self.logger.view_logs(lines)
    
    def export_logs(self, current_user: str = "") -> tuple[bool, str]:
        """Export logs to CSV (admin only). Returns (success: bool, message: str)."""
        success, message = self.logger.export_to_csv()
        
        if success:
            self.logger.log_command(current_user, "export_logs", True)
            self.logger.log_admin_action(current_user, "export_logs")
        
        return success, message
    
    def unlock_user(self, username: str, current_user: str = "") -> tuple[bool, str]:
        """Unlock a user account (admin only). Returns (success: bool, message: str)."""
        if not username:
            return False, "Username is required"
        
        success, message = self.auth.unlock_user(username)
        
        if success:
            self.logger.log_admin_action(current_user, "unlock_user", username)
            self.logger.log_command(current_user, f"unlock_user {username}", True)
        
        return success, message


