"""
Authentication Module
Handles user authentication, password hashing, and account lockout.
"""
import json
import os
import hashlib
from typing import Optional, Dict, Any


class AuthModule:
    """Manages user authentication and user storage."""
    
    USERS_FILE = "users.json"
    MAX_FAILED_ATTEMPTS = 3
    
    def __init__(self):
        """Initialize the authentication module."""
        self.users_file = self.USERS_FILE
        self.lockout_state: Dict[str, int] = {}  # username -> failed attempts
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Create users.json if it doesn't exist."""
        if not os.path.exists(self.users_file):
            # Create default admin user
            default_users = {
                "admin": {
                    "password_hash": self._hash_password("admin123"),
                    "role": "admin",
                    "locked": False
                }
            }
            self._save_users(default_users)
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _load_users(self) -> Dict[str, Any]:
        """Load users from JSON file."""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_users(self, users: Dict[str, Any]):
        """Save users to JSON file."""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def authenticate(self, username: str, password: str) -> tuple[bool, str]:
        """
        Authenticate a user.
        
        Returns:
            (success: bool, message: str)
        """
        users = self._load_users()
        
        if username not in users:
            return False, "Invalid username or password"
        
        user = users[username]
        
        # Check if account is locked
        if user.get("locked", False):
            return False, "Account is locked. Please contact an administrator."
        
        # Check lockout state
        failed_attempts = self.lockout_state.get(username, 0)
        if failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            user["locked"] = True
            self._save_users(users)
            return False, "Account locked due to too many failed login attempts."
        
        # Verify password
        password_hash = self._hash_password(password)
        if user["password_hash"] != password_hash:
            # Increment failed attempts
            self.lockout_state[username] = failed_attempts + 1
            remaining = self.MAX_FAILED_ATTEMPTS - (failed_attempts + 1)
            if remaining > 0:
                return False, f"Invalid password. {remaining} attempt(s) remaining."
            else:
                user["locked"] = True
                self._save_users(users)
                return False, "Account locked due to too many failed login attempts."
        
        # Successful login - reset failed attempts
        self.lockout_state[username] = 0
        return True, "Login successful"
    
    def get_user_role(self, username: str) -> Optional[str]:
        """Get the role of a user."""
        users = self._load_users()
        if username in users:
            return users[username].get("role", "user")
        return None
    
    def user_exists(self, username: str) -> bool:
        """Check if a user exists."""
        users = self._load_users()
        return username in users
    
    def add_user(self, username: str, password: str, role: str = "user") -> tuple[bool, str]:
        """
        Add a new user.
        
        Returns:
            (success: bool, message: str)
        """
        users = self._load_users()
        
        if username in users:
            return False, f"User '{username}' already exists"
        
        if role not in ["admin", "user"]:
            return False, "Role must be 'admin' or 'user'"
        
        users[username] = {
            "password_hash": self._hash_password(password),
            "role": role,
            "locked": False
        }
        
        self._save_users(users)
        return True, f"User '{username}' added successfully"
    
    def remove_user(self, username: str) -> tuple[bool, str]:
        """
        Remove a user.
        
        Returns:
            (success: bool, message: str)
        """
        users = self._load_users()
        
        if username not in users:
            return False, f"User '{username}' does not exist"
        
        del users[username]
        self._save_users(users)
        
        # Clear lockout state if exists
        if username in self.lockout_state:
            del self.lockout_state[username]
        
        return True, f"User '{username}' removed successfully"
    
    def unlock_user(self, username: str) -> tuple[bool, str]:
        """
        Unlock a user account.
        
        Returns:
            (success: bool, message: str)
        """
        users = self._load_users()
        
        if username not in users:
            return False, f"User '{username}' does not exist"
        
        users[username]["locked"] = False
        self._save_users(users)
        
        # Reset lockout state
        if username in self.lockout_state:
            self.lockout_state[username] = 0
        
        return True, f"User '{username}' unlocked successfully"
    
    def change_password(self, username: str, old_password: str, new_password: str) -> tuple[bool, str]:
        """
        Change a user's password.
        
        Returns:
            (success: bool, message: str)
        """
        users = self._load_users()
        
        if username not in users:
            return False, "User does not exist"
        
        user = users[username]
        
        # Verify old password
        old_password_hash = self._hash_password(old_password)
        if user["password_hash"] != old_password_hash:
            return False, "Current password is incorrect"
        
        # Update password
        user["password_hash"] = self._hash_password(new_password)
        self._save_users(users)
        
        return True, "Password changed successfully"
    
    def get_all_users(self) -> Dict[str, Any]:
        """Get all users (for admin purposes)."""
        return self._load_users()

