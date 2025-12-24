"""
Main Entry Point
Multi-User Access Control System with CLI and Voice Support
"""
import getpass
from auth import AuthModule
from session import SessionManager
from logger import Logger
from admin import AdminTools
from command_dispatcher import CommandDispatcher
from voice import VoiceIntegration


class AccessControlSystem:
    """Main system class integrating all modules."""
    
    def __init__(self):
        """Initialize the access control system."""
        self.auth = AuthModule()
        self.session = SessionManager()
        self.logger = Logger()
        self.admin = AdminTools(self.auth, self.logger)
        self.dispatcher = CommandDispatcher(self.session, self.auth, self.admin, self.logger)
        self.voice = VoiceIntegration()
    
    def login(self) -> bool:
        """Handle user login. Returns True if successful."""
        print("\n=== Login ===")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        
        if not username or not password:
            print("Username and password are required.")
            return False
        
        success, message = self.auth.authenticate(username, password)
        self.logger.log_login_attempt(username, success)
        
        if not success:
            print(f"\n{message}")
            return False
        
        # Login successful - create session
        role = self.auth.get_user_role(username)
        self.session.create_session(username, role)
        print(f"\n{message}")
        print(f"Welcome, {username}! (Role: {role})")
        return True
    
    def run(self):
        """Main application loop."""
        print("=" * 50)
        print("Multi-User Access Control System")
        print("=" * 50)
        
        # Login loop
        while not self.session.is_authenticated():
            if not self.login():
                retry = input("\nTry again? (y/n): ").strip().lower()
                if retry != 'y':
                    print("Goodbye!")
                    return
        
        # Main command loop
        self._show_welcome_message()
        voice_mode = False
        
        while self.session.is_authenticated():
            try:
                command, args = self._get_user_command(voice_mode)
                
                if command is None:
                    # In voice mode, continue asking for commands
                    # In text mode, just continue the loop
                    if not voice_mode:
                        continue
                    # If in voice mode and command is None, ask again
                    continue
                
                # Handle voice mode activation
                if command == "VOICE_MODE":
                    voice_mode = True
                    continue
                
                # Handle exit voice mode command
                if command == "exit voice mode":
                    voice_mode = False
                    print("\nExited voice mode. Returning to text mode.\n")
                    continue
                
                # Execute command
                success, message = self.dispatcher.execute_command(command, args)
                
                # Handle logout
                if self._is_logout_command(success, message):
                    print(f"\n{message}")
                    break
                
                print(f"\n{message}\n")
                
                # In voice mode, continue asking for next command
                if voice_mode:
                    print("Voice mode active. Speak your next command or say 'exit voice mode' to return to text mode.\n")
            
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'logout' to exit or continue with commands.")
            except EOFError:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                username = self.session.get_current_user()
                self.logger.log_error(username, f"Error: {str(e)}")
                print(f"An error occurred: {e}")
        
        print("\nSession ended. Goodbye!")
    
    def _show_welcome_message(self):
        """Display welcome message with available commands."""
        print("\nType 'help' for available commands.")
        print("Type 'voice' to enter voice command mode.")
        print("Type 'logout' to exit.\n")
    
    def _get_user_command(self, voice_mode: bool) -> tuple:
        """Get command from user (voice or text). Returns (command, args) or (None, None)."""
        if voice_mode:
            return self._handle_voice_command()
        else:
            return self._handle_text_command()
    
    def _handle_voice_command(self) -> tuple:
        """Handle voice command input."""
        command = self.voice.listen_for_command()
        if command is None:
            print("No command recognized. Please try again.\n")
            return None, None
        print(f"Executing voice command: {command}")
        return command, []
    
    def _handle_text_command(self) -> tuple:
        """Handle text command input."""
        user_input = input(f"{self.session.get_current_user()}> ").strip()
        
        if not user_input:
            return None, None
        
        # Check for voice mode activation
        if user_input.lower() == "voice":
            if self.voice.is_voice_available():
                print("\n=== Voice Mode Activated ===")
                print("Speak your commands clearly. Say 'help' to see available commands.")
                print("Say 'exit voice mode' to return to text mode.")
                print("The system will listen for 5 seconds after you speak.\n")
                # Return a special marker to indicate voice mode
                return "VOICE_MODE", []
            else:
                print("Voice recognition not available.")
                print("Please check your microphone connection and try again.")
                return None, None
        
        return self.dispatcher.parse_command(user_input)
    
    def _is_logout_command(self, success: bool, message: str) -> bool:
        """Check if the command was a successful logout."""
        return success and message == "Logged out successfully"


def main():
    """Entry point."""
    system = AccessControlSystem()
    system.run()


if __name__ == "__main__":
    main()

