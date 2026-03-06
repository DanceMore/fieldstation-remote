import json
import os
import utils

class StateManager:
    """Manages persistent state for the FieldStation Remote"""
    
    def __init__(self, state_file=None):
        if state_file is None:
            # Default to runtime/state.json
            base_path = os.environ.get("FIELDSTATION_RUNTIME", "runtime")
            state_file = os.path.join(base_path, "state.json")
            
        self.state_file = state_file
        self.data = {
            "current_channel": 1,
            "last_update": 0
        }
        self.load()

    def load(self):
        """Load state from disk with graceful fallback"""
        if not os.path.exists(self.state_file):
            return False
            
        try:
            with open(self.state_file, 'r') as f:
                loaded_data = json.load(f)
                # Merge into default data to ensure all keys exist
                self.data.update(loaded_data)
                return True
        except Exception as e:
            print(f"⚠️ Failed to load state: {e}")
            return False

    def save(self):
        """Atomic save to disk using os.replace"""
        self.data["last_update"] = utils.get_now()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        tmp_file = self.state_file + ".tmp"
        try:
            with open(tmp_file, 'w') as f:
                json.dump(self.data, f, indent=2)
                f.flush()
                os.fsync(f.fileno()) # Ensure it's on silicon
            
            # Atomic swap
            os.replace(tmp_file, self.state_file)
            return True
        except Exception as e:
            print(f"⚠️ Failed to save state: {e}")
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
            return False

    def update(self, **kwargs):
        """Update multiple state keys and save immediately"""
        self.data.update(kwargs)
        return self.save()

    def get(self, key, default=None):
        """Get a value from state"""
        return self.data.get(key, default)
