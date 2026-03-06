# Spec: State Persistence (0005)

## Reality
Currently, `current_channel` is initialized to `VALID_CHANNELS[0]` in `ChannelDialer.__init__`. If the process restarts, all history is lost.

## Intent
Implement a `StateManager` class that handles the lifecycle of the system's volatile data.
- **Storage**: Flat JSON file at `runtime/state.json`.
- **Atomic Writes**: To prevent half-written files during power loss, write to `state.json.tmp` and use `os.replace()` to overwrite the original.
- **Data Schema**:
  ```json
  {
    "current_channel": 1,
    "last_update": 1772767982.0
  }
  ```

## Learning
Art installations often have "dirty" power. Standard file writes are dangerous because a power cut during the `write()` call leaves a 0-byte or corrupted file. Atomic `os.replace` is the standard "Best Practice" for embedded Linux appliances to ensure the state file is either the "Old Version" or the "New Version," but never "Corrupted."
