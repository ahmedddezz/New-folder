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
        """
        Handle user login.
        
        Returns:
            True if login successful, False otherwise
        """
        print("\n=== Login ===")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        
        if not username or not password:
            print("Username and password are required.")
            return False
        
        success, message = self.auth.authenticate(username, password)
        self.logger.log_login_attempt(username, success)
        
        if success:
            role = self.auth.get_user_role(username)
            token = self.session.create_session(username, role)
            print(f"\n{message}")
            print(f"Welcome, {username}! (Role: {role})")
            return True
        else:
            print(f"\n{message}")
            return False
    
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
        print("\nType 'help' for available commands.")
        print("Type 'voice' to enter voice command mode.")
        print("Type 'logout' to exit.\n")
        
        voice_mode = False
        
        while self.session.is_authenticated():
            try:
                if voice_mode:
                    command = self.voice.listen_for_command()
                    if command is None:
                        print("No command recognized. Switching to text mode.")
                        voice_mode = False
                        continue
                    print(f"Executing voice command: {command}")
                    # For voice commands, check if additional args are needed
                    args = []
                    # Commands that need arguments will prompt for them in their handlers
                else:
                    user_input = input(f"{self.session.get_current_user()}> ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Check for voice mode
                    if user_input.lower() == "voice":
                        if self.voice.is_voice_available():
                            voice_mode = True
                            print("Voice mode activated. Speak your commands.")
                            continue
                        else:
                            print("Voice recognition not available.")
                            continue
                    
                    command, args = self.dispatcher.parse_command(user_input)
                
                # Execute command
                success, message = self.dispatcher.execute_command(command, args)
                
                # Check if logout was successful
                if success and message == "Logged out successfully":
                    print(f"\n{message}")
                    break
                
                print(f"\n{message}\n")
                
                # Exit voice mode after command
                if voice_mode:
                    voice_mode = False
                    print("Returned to text mode.")
            
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


def main():
    """Entry point."""
    system = AccessControlSystem()
    system.run()


if __name__ == "__main__":
    main()

