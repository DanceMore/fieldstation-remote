# Feature: IR Remote Mapping (F-001)

## Intent
The physical interface of the "Wilderness Appliance" is an infrared remote. This feature maps raw, hardware-specific IR signals (NEC, Samsung, Sony) into standardized, high-level events that the backend can understand.

## Success Criteria
- **Protocol Independence**: The system handles multiple IR protocols without the rest of the application needing to know the details.
- **Deduplication**: Rapid IR repeats are debounced to prevent "double-click" effects.
- **Extensibility**: New remotes can be added by editing a centralized configuration.

## Intent Vectors
- **Tactile Reliability**: Button presses must feel immediate and "correct."
- **Backward Compatibility**: Supports both custom Arduino hardware and Flipper Zero as a backup.
