#!/usr/bin/env python3
import time
import random

class MockSerial:
    def __init__(self, port, baudrate, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.is_open = True
        print(f"DEBUG [MockSerial]: Connected to {port} @ {baudrate}")

    def write(self, data):
        print(f"DEBUG [MockSerial] {self.port} <WRITE>: {data!r}")
        return len(data)

    def flush(self):
        pass

    def flushInput(self):
        pass

    def close(self):
        self.is_open = False
        print(f"DEBUG [MockSerial] {self.port} <CLOSE>")

    def readline(self):
        # If this is the Flipper Zero device, we can simulate some IR signals
        if "ACM0" in self.port or "device" in self.port:
            time.sleep(random.uniform(0.1, 2.0))
            # Simulate some random IR signals from the configs
            signals = [
                "NEC, A:0x32, C:0x00", # DIGIT_0
                "NEC, A:0x32, C:0x01", # DIGIT_1
                "NEC, A:0x32, C:0x11", # CHANNEL_UP
                "Samsung32, A:0x07, C:0x04", # DIGIT_1
                "SIRC, A:0x01, C:0x10", # CHANNEL_UP
            ]
            signal = random.choice(signals)
            print(f"DEBUG [MockSerial] {self.port} <READLINE>: {signal}")
            return (signal + "\r\n").encode('utf-8')
        
        # For other devices (like the display), we don't expect to read anything
        time.sleep(self.timeout)
        return b""
