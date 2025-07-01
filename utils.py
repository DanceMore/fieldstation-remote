#!/usr/bin/env python3
"""
Utility functions shared across the channel dialer system
"""

import subprocess
import json

# Configuration that might be shared
SOCKET_PATH = "/home/appuser/FieldStation42/runtime/channel.socket"

def safe_execute(func, error_msg="Operation failed"):
    """Decorator for safe function execution with error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"{error_msg}: {e}")
            return None
    return wrapper

@safe_execute
def write_json_to_socket(data):
    """Write JSON data to socket"""
    json_str = json.dumps(data)
    with open(SOCKET_PATH, 'w') as f:
        f.write(json_str)
    print(f"JSON written: {json_str}")

@safe_execute
def send_key_to_mpv(key):
    """Send key to mpv window"""
    window_id = subprocess.check_output(
        ['xdotool', 'search', '--onlyvisible', '--class', 'mpv'],
        env={'DISPLAY': ':0'}
    ).decode().strip().split('\n')[0]
    subprocess.run(['xdotool', 'key', '--window', window_id, key], env={'DISPLAY': ':0'})
    print(f"Sent key '{key}' to MPV")
