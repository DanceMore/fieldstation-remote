import threading
import time
from queue import Queue, Empty

class DisplayQueue:
    def __init__(self, display_controller):
        self.display_controller = display_controller
        self.queue = Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self._stop = threading.Event()

    def start(self):
        self.thread.start()

    def stop(self):
        self.queue.put(("__EXIT__", None))
        self._stop.set()
        self.thread.join(timeout=2)

    def _worker(self):
        while not self._stop.is_set():
            try:
                cmd, value = self.queue.get(timeout=1)
                if cmd == "__EXIT__":
                    break
                if cmd == "text":
                    self.display_controller.display_text(value)
                elif cmd == "number":
                    self.display_controller.display_number(value)
                elif cmd == "clear":
                    self.display_controller.clear_display()
                elif cmd == "brightness":
                    self.display_controller.set_brightness(value)
                elif cmd == "sleep":
                    time.sleep(value)
            except Empty:
                continue

    def show_text(self, text):
        self.queue.put(("text", text))

    def show_number(self, number):
        self.queue.put(("number", number))

    def clear(self):
        self.queue.put(("clear", None))

    def sleep(self, seconds):
        self.queue.put(("sleep", seconds))

    def set_brightness(self, level):
        self.queue.put(("brightness", level))
