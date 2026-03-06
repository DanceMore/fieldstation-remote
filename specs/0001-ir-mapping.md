# Spec: IR Remote Mapping (0001)

## Reality
Implemented in `flipper_ir_remote.py` via the `REMOTE_CONFIGS` dictionary. 
- **Matching**: The system listens for serial strings in the format `Protocol, A:Address, C:Command`.
- **Deduplication**: Uses a `debounce` timer (default 0.7s) to ignore identical rapid-fire signals from IR repeats.
- **Protocols**: Currently supports NEC (0x32), Samsung32 (0x07), Sony SIRC (0x01), and special Sony variants (0x77, 0x97).

## Intent
Decouple physical silicon from digital logic. The application should only care about `CHANNEL_UP` or `DIGIT_1`, regardless of whether it came from a vintage Sony remote or a modern Flipper Zero.

## Learning
Raw IR is noisy. A software-level debounce is required because physical remotes often blast 5-10 repeat packets for a single "click." By mapping these to standardized event strings, the rest of the application remains protocol-agnostic.
