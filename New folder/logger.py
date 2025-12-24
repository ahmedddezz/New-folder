"""
Logging Module
Handles logging of commands and login attempts.
"""
import os
from datetime import datetime
from typing import Optional
import csv


class Logger:
    """Manages system logging."""
    
    LOG_FILE = "logs.txt"
    CSV_LOG_FILE = "logs.csv"
    
    def __init__(self):
        """Initialize the logger."""
        self.log_file = self.LOG_FILE
        self.csv_log_file = self.CSV_LOG_FILE
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Create log file if it doesn't exist."""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write("=== System Logs ===\n")
    
    def _write_log(self, level: str, message: str, username: Optional[str] = None):
        """Write a log entry to the log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_str = f" [{username}]" if username else ""
        log_entry = f"[{timestamp}] [{level}]{user_str} {message}\n"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
    
    def log_login_attempt(self, username: str, success: bool):
        """Log a login attempt."""
        status = "SUCCESS" if success else "FAILED"
        self._write_log("LOGIN", f"Login attempt {status} for user: {username}", username)
    
    def log_command(self, username: str, command: str, success: bool = True):
        """Log a command execution."""
        status = "SUCCESS" if success else "FAILED"
        self._write_log("COMMAND", f"Command '{command}' executed - {status}", username)
    
    def log_admin_action(self, username: str, action: str, target: Optional[str] = None):
        """Log an admin action."""
        target_str = f" on {target}" if target else ""
        self._write_log("ADMIN", f"Admin action: {action}{target_str}", username)
    
    def log_error(self, username: Optional[str], error: str):
        """Log an error."""
        self._write_log("ERROR", error, username)
    
    def view_logs(self, lines: Optional[int] = None) -> str:
        """
        View logs from the log file.
        
        Args:
            lines: Number of recent lines to return (None for all)
        
        Returns:
            log content as string
        """
        try:
            with open(self.log_file, 'r') as f:
                all_lines = f.readlines()
            
            if lines is None:
                return ''.join(all_lines)
            else:
                return ''.join(all_lines[-lines:])
        except FileNotFoundError:
            return "No logs found."
    
    def export_to_csv(self) -> tuple[bool, str]:
        """Export logs to CSV format. Returns (success: bool, message: str)."""
        try:
            log_lines = self._read_log_lines()
            csv_data = self._parse_logs_to_csv(log_lines)
            self._write_csv_file(csv_data)
            return True, f"Logs exported to {self.csv_log_file}"
        except Exception as e:
            return False, f"Failed to export logs: {str(e)}"
    
    def _read_log_lines(self) -> list:
        """Read all lines from the log file."""
        with open(self.log_file, 'r') as f:
            return f.readlines()
    
    def _parse_logs_to_csv(self, log_lines: list) -> list:
        """Parse log lines into CSV format."""
        csv_data = [["Timestamp", "Level", "Username", "Message"]]
        
        for line in log_lines:
            line = line.strip()
            if not line or line.startswith("==="):
                continue
            
            parsed_entry = self._parse_log_line(line)
            if parsed_entry:
                csv_data.append(parsed_entry)
        
        return csv_data
    
    def _parse_log_line(self, line: str) -> Optional[list]:
        """Parse a single log line. Returns [timestamp, level, username, message] or None."""
        if not line.startswith("["):
            return None
        
        try:
            # Extract timestamp: [timestamp]
            end_timestamp = line.find("]", 1)
            timestamp = line[1:end_timestamp]
            
            # Extract level: [LEVEL]
            start_level = line.find("[", end_timestamp + 1)
            end_level = line.find("]", start_level + 1)
            level = line[start_level + 1:end_level]
            
            # Extract username (optional) and message
            remaining = line[end_level + 1:].strip()
            username = ""
            message = remaining
            
            if remaining.startswith("["):
                end_username = remaining.find("]", 1)
                username = remaining[1:end_username]
                message = remaining[end_username + 1:].strip()
            
            return [timestamp, level, username, message]
        except Exception:
            return None
    
    def _write_csv_file(self, csv_data: list):
        """Write CSV data to file."""
        with open(self.csv_log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

