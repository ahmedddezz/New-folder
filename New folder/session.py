"""
Session Manager
Tracks current user sessions and provides session token management.
"""
from typing import Optional, Dict
from datetime import datetime
import secrets


class SessionManager:
    """Manages user sessions and tokens."""
    
    def __init__(self):
        """Initialize the session manager."""
        self.sessions: Dict[str, Dict] = {}  # token -> session data
        self.current_token: Optional[str] = None
    
    def create_session(self, username: str, role: str) -> str:
        """
        Create a new session for a user.
        
        Returns:
            session_token: str
        """
        token = secrets.token_urlsafe(32)
        self.sessions[token] = {
            "username": username,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        self.current_token = token
        return token
    
    def get_current_user(self) -> Optional[str]:
        """Get the username of the current session."""
        session_data = self._get_current_session()
        return session_data["username"] if session_data else None
    
    def get_current_role(self) -> Optional[str]:
        """Get the role of the current session."""
        session_data = self._get_current_session()
        return session_data["role"] if session_data else None
    
    def _get_current_session(self) -> Optional[Dict]:
        """Get the current session data if it exists."""
        if self.current_token and self.current_token in self.sessions:
            return self.sessions[self.current_token]
        return None
    
    def is_authenticated(self) -> bool:
        """Check if there is an active session."""
        return self.current_token is not None and self.current_token in self.sessions
    
    def is_admin(self) -> bool:
        """Check if the current user is an admin."""
        return self.get_current_role() == "admin"
    
    def update_activity(self):
        """Update the last activity time for the current session."""
        session_data = self._get_current_session()
        if session_data:
            session_data["last_activity"] = datetime.now().isoformat()
    
    def end_session(self):
        """End the current session."""
        if self.current_token:
            if self.current_token in self.sessions:
                del self.sessions[self.current_token]
            self.current_token = None
    
    def get_session_info(self) -> Optional[Dict]:
        """Get information about the current session."""
        session_data = self._get_current_session()
        return session_data.copy() if session_data else None

