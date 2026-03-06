# Spec: 7-Segment Display Queue (0004)

## Reality
Logic split between `display_controller.py` (low-level serial) and `display_queue.py` (high-level thread).
- **Worker**: A background `threading.Thread` pulling from a `queue.Queue`.
- **Latency**: Uses `utils.sleep` for command pacing (e.g., 0.1s for init).
- **Communication**: Sends standard ASCII strings (`DISP:xxxx`) over Serial.

## Intent
Decouple the UI from the event loop. The physical Arduino/TM1637 display is slow (115200 baud but constrained processing). We must never block the IR receiver thread while waiting for a display serial write to flush.

## Learning
Synchronous display writes cause dropped IR frames. Physical remotes send pulses very quickly; if the Python thread is busy waiting for a "flush" on the display serial port, the Linux kernel serial buffer for the IR receiver can overflow or skip. The background queue is mandatory for responsiveness.
