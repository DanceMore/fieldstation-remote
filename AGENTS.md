# Agentic Standards for FieldStation Remote

## 🏗️ The Verification Loop
- **Primary Command**: `python3 test_logic.py && python3 test_time_sensitive.py`
- **Requirement**: All new features MUST include a deterministic test case in `test_logic.py` or a new test file.

## 🎭 The Sandbox Rule (Puppeteer Model)
This project uses a "Puppeteer" abstraction to simulate hardware and time. 
- **Time**: Never use `time.time()`. Use `utils.get_now()`.
- **Delays**: Never use `time.sleep()`. Use `utils.sleep()`.
- **Timers**: Never use `threading.Timer()`. Use `utils.start_timer()`.
- **IO**: Check `utils.IS_MOCK` before calling `xdotool` or writing to system sockets.

## 💾 State & Persistence
- Local state lives in `runtime/`. 
- Do not assume paths like `/home/appuser/` exist; use relative paths or `os.makedirs`.

## 📜 Repository Tribal Knowledge
- **Early Returns**: We prefer early returns to reduce nesting.
- **Mocks**: Mocks for hardware (Serial/Display) live in `mock_serial.py`.
- **Interception**: Global time/timer interception is managed in `utils.py` via `set_time_source` and `set_timer_source`.
