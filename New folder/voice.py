"""
Voice Integration Module
Maps spoken words to commands.
"""
import speech_recognition as sr
from typing import Optional, Dict, List


class VoiceIntegration:
    """Handles voice command recognition and mapping."""
    
    # Command mappings: spoken words -> command
    COMMAND_MAP = {
        "status": ["status", "state", "info", "information"],
        "logout": ["logout", "log out", "quit", "sign out"],
        "help": ["help", "commands", "menu"],
        "add user": ["add user", "create user", "new user"],
        "remove user": ["remove user", "delete user"],
        "unlock user": ["unlock user", "unlock account", "unlock"],
        "view logs": ["view logs", "show logs", "logs", "log"],
        "change password": ["change password", "update password", "modify password"],
        "export logs": ["export logs", "export", "save logs"],
        "exit voice mode": ["exit voice mode", "exit voice", "leave voice mode", "stop voice", "back to text"]
    }
    
    def __init__(self):
        """Initialize the voice recognition system."""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self._calibrate_microphone()
    
    def _calibrate_microphone(self):
        """Calibrate the microphone for ambient noise."""
        try:
            print("Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Microphone calibrated successfully.")
        except Exception as e:
            print(f"Warning: Could not calibrate microphone: {e}")
            print("Voice recognition may still work, but accuracy might be reduced.")
    
    def listen_for_command(self, timeout: int = 5) -> Optional[str]:
        """
        Listen for a voice command.
        
        Args:
            timeout: Maximum time to wait for input (seconds)
        
        Returns:
            recognized command string or None
        """
        try:
            with self.microphone as source:
                print("Listening for voice command... (speak now)")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
            
            try:
                # Use Google Speech Recognition
                text = self.recognizer.recognize_google(audio).lower()
                print(f"Recognized text: '{text}'")
                command = self._map_to_command(text)
                if command:
                    print(f"Mapped to command: '{command}'")
                return command
            except sr.UnknownValueError:
                print("Could not understand audio. Please speak more clearly.")
                return None
            except sr.RequestError as e:
                print(f"Error: Could not request results from speech recognition service.")
                print(f"Details: {e}")
                print("Make sure you have an internet connection for Google Speech Recognition.")
                return None
        except sr.WaitTimeoutError:
            print("No voice input detected within timeout period.")
            return None
        except Exception as e:
            print(f"Error in voice recognition: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return None
    
    def _map_to_command(self, spoken_text: str) -> Optional[str]:
        """Map spoken text to a command. Returns command string or None."""
        spoken_text = spoken_text.lower().strip()
        
        # Try exact match first (most reliable)
        if spoken_text in self.COMMAND_MAP:
            return spoken_text
        
        # Try direct command match (command name is substring of spoken text)
        for command in self.COMMAND_MAP.keys():
            if command in spoken_text:
                return command
        
        # Try keyword matching (any keyword is substring of spoken text)
        for command, keywords in self.COMMAND_MAP.items():
            for keyword in keywords:
                if keyword in spoken_text:
                    return command
        
        # Debug: show what was recognized but not matched
        print(f"Warning: Could not map '{spoken_text}' to any command")
        print(f"Available commands: {', '.join(self.COMMAND_MAP.keys())}")
        return None
    
    def get_available_commands(self) -> List[str]:
        """Get list of available voice commands."""
        return list(self.COMMAND_MAP.keys())
    
    def is_voice_available(self) -> bool:
        """Check if voice recognition is available."""
        try:
            # Test if microphone is accessible
            with self.microphone as source:
                # Test if recognizer is ready
                if self.recognizer is None:
                    return False
                return True
        except Exception as e:
            print(f"Voice recognition not available: {e}")
            print("Make sure your microphone is connected and not being used by another application.")
            return False

