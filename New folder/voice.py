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
        "logout": ["logout", "log out", "exit", "quit", "sign out"],
        "help": ["help", "commands", "menu"],
        "add user": ["add user", "create user", "new user"],
        "remove user": ["remove user", "delete user"],
        "view logs": ["view logs", "show logs", "logs", "log"],
        "change password": ["change password", "update password", "modify password"],
        "export logs": ["export logs", "export", "save logs"]
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
            print("Microphone calibrated.")
        except Exception as e:
            print(f"Warning: Could not calibrate microphone: {e}")
    
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
                print("Listening for voice command...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
            
            try:
                # Use Google Speech Recognition
                text = self.recognizer.recognize_google(audio).lower()
                print(f"Recognized: {text}")
                return self._map_to_command(text)
            except sr.UnknownValueError:
                print("Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"Could not request results from speech recognition service: {e}")
                return None
        except sr.WaitTimeoutError:
            print("No voice input detected")
            return None
        except Exception as e:
            print(f"Error in voice recognition: {e}")
            return None
    
    def _map_to_command(self, spoken_text: str) -> Optional[str]:
        """
        Map spoken text to a command.
        
        Args:
            spoken_text: The recognized speech text
        
        Returns:
            command string or None
        """
        spoken_text = spoken_text.lower().strip()
        
        # Direct match
        for command, keywords in self.COMMAND_MAP.items():
            if command in spoken_text:
                return command
        
        # Keyword matching
        for command, keywords in self.COMMAND_MAP.items():
            for keyword in keywords:
                if keyword in spoken_text:
                    return command
        
        return None
    
    def get_available_commands(self) -> List[str]:
        """Get list of available voice commands."""
        return list(self.COMMAND_MAP.keys())
    
    def is_voice_available(self) -> bool:
        """Check if voice recognition is available."""
        try:
            with self.microphone as source:
                return True
        except:
            return False

