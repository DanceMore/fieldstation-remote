#!/usr/bin/env python3
import random
import os
import utils

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
            utils.sleep(random.uniform(0.1, 2.0))

            # Chaos mode: Inject garbage data 30% of the time
            if os.environ.get("CHAOS_MODE") == "true" and random.random() < 0.3:
                chaos_types = [
                    "MALFORMED_HEX",
                    "PARTIAL_LINE",
                    "PROTOCOL_VIOLATION",
                    "NOISE"
                ]
                chaos_type = random.choice(chaos_types)

                if chaos_type == "MALFORMED_HEX":
                    signal = "NEC, A:0xZZ, C:0x11"
                elif chaos_type == "PARTIAL_LINE":
                    signal = "Samsung32, A:0x07"
                elif chaos_type == "PROTOCOL_VIOLATION":
                    signal = "UNKNOWN_PROTO, A:0x01, C:0x02"
                else: # NOISE
                    print(f"DEBUG [MockSerial] {self.port} <READLINE>: <RANDOM NOISE>")
                    return os.urandom(10) + b"\r\n"

                print(f"DEBUG [MockSerial] {self.port} <READLINE> (CHAOS): {signal}")
                return (signal + "\r\n").encode('utf-8')

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
        utils.sleep(self.timeout)
        return b""
