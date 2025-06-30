"""
Socket communication utilities for writing JSON data to the channel socket.
"""

import json
import time
from typing import Dict, Any, Optional
from config.settings import SOCKET_PATH


def write_json_to_socket(data: Dict[str, Any]) -> bool:
    """
    Write JSON data to the socket file.
    
    Args:
        data: Dictionary to write as JSON
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = time.time()
            
        json_str = json.dumps(data)
        with open(SOCKET_PATH, 'w') as f:
            f.write(json_str)
        print(f"📡 JSON written: {json_str}")
        return True
    except Exception as e:
        print(f"❌ Error writing to socket: {e}")
        return False


def write_channel_command(command: str, channel: Optional[int] = None, 
                         valid: Optional[bool] = None, **kwargs) -> bool:
    """
    Write a channel-related command to the socket.
    
    Args:
        command: Command type (e.g., 'direct', 'up', 'down')
        channel: Channel number (if applicable)
        valid: Whether the channel is valid (if applicable)
        **kwargs: Additional data to include
        
    Returns:
        bool: True if successful, False otherwise
    """
    data = {
        "command": command,
        **kwargs
    }
    
    if channel is not None:
        data["channel"] = channel
    if valid is not None:
        data["valid"] = valid
        
    return write_json_to_socket(data)


def write_power_command() -> bool:
    """Write a power toggle command to the socket."""
    return write_json_to_socket({"command": "power_toggle"})


def write_info_command() -> bool:
    """Write an info command to the socket."""
    return write_json_to_socket({"command": "info"})


def write_menu_command() -> bool:
    """Write a menu command to the socket."""
    return write_json_to_socket({"command": "menu"})


def write_back_command() -> bool:
    """Write a back command to the socket."""
    return write_json_to_socket({"command": "back"})


def write_no_handler_event(event_name: str) -> bool:
    """Write a no-handler event to the socket."""
    return write_json_to_socket({
        "command": "no_handler", 
        "event": event_name
    })
