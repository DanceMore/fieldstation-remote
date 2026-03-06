import os
import subprocess
import json
import time
import threading

# Configuration that might be shared
SOCKET_PATH = "/home/appuser/FieldStation42/runtime/channel.socket"
IS_MOCK = os.environ.get("MOCK_MODE", "false").lower() == "true"

# --- Transparent Time Interception ---
# These can be swapped out by the test suite to control "reality"
_time_source = time.time
_sleep_source = time.sleep
_timer_source = threading.Timer

def get_now():
    """Project-wide 'now' - defaults to real time"""
    return _time_source()

def sleep(seconds):
    """Project-wide 'sleep' - defaults to real sleep"""
    return _sleep_source(seconds)

def start_timer(interval, function, args=None, kwargs=None):
    """Project-wide 'Timer' - defaults to threading.Timer"""
    t = _timer_source(interval, function, args=args, kwargs=kwargs)
    t.start()
    return t

# --- Test Harness Hooks (Only used by tests) ---
def set_time_source(func): global _time_source; _time_source = func
def set_sleep_source(func): global _sleep_source; _sleep_source = func
def set_timer_source(func): global _timer_source; _timer_source = func

# --- Existing Utilities ---
def safe_execute(func, error_msg="Operation failed"):
    """Decorator for safe function execution with error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if not IS_MOCK:
                print(f"{error_msg}: {e}")
            return None
    return wrapper

@safe_execute
def write_json_to_socket(data):
    """Write JSON data to socket"""
    json_str = json.dumps(data)
    if IS_MOCK:
        print(f"DEBUG [MockSocket] Write to {SOCKET_PATH}: {json_str}")
        return
        
    os.makedirs(os.path.dirname(SOCKET_PATH), exist_ok=True)
    with open(SOCKET_PATH, 'w') as f:
        f.write(json_str)
    print(f"JSON written: {json_str}")

@safe_execute
def send_key_to_mpv(key):
    """Send key to mpv window"""
    if IS_MOCK:
        print(f"DEBUG [MockXdotool] Send key '{key}' to MPV")
        return

    window_id = subprocess.check_output(
        ['xdotool', 'search', '--onlyvisible', '--class', 'mpv'],
        env={'DISPLAY': ':0'}
    ).decode().strip().split('\n')[0]
    subprocess.run(['xdotool', 'key', '--window', window_id, key], env={'DISPLAY': ':0'})
    print(f"Sent key '{key}' to MPV")
