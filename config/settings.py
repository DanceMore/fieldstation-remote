#!/usr/bin/env python3
"""
Configuration settings for IR Remote Mapper
"""

import os

# File paths
SOCKET_PATH = "/home/appuser/FieldStation42/runtime/channel.socket"
LOG_PATH = "/home/appuser/FieldStation42/runtime/ir_mapper.log"

# Serial communication settings
DEFAULT_FLIPPER_DEVICE = "/dev/ttyACM0"
DEFAULT_DISPLAY_DEVICE = "/dev/ttyACM0"
DEFAULT_DISPLAY_BAUDRATE = 9600
FLIPPER_BAUDRATE = 115200

# Timing settings
DEFAULT_DEBOUNCE_TIME = 0.7
DEFAULT_DIGIT_TIMEOUT = 1.5
DEFAULT_EASTER_EGG_TIMEOUT = 1.5

# Display settings
DEFAULT_DISPLAY_BRIGHTNESS = 7
DISPLAY_INIT_DELAY = 0.1
DISPLAY_COMMAND_DELAY = 0.5

# Channel settings
VALID_CHANNELS = [1, 2, 3, 8, 9, 13]
DEFAULT_CHANNEL = 1

# Boot sequence settings
BOOT_SEQUENCE = [
    ("----", 0.8),
    ("ACId", 0.4), 
    ("BOOT", 2.0),
    ("redY", 1.5)
]

# Easter egg display timings
EASTER_EGG_DISPLAY_TIME = 1.0
ERROR_DISPLAY_TIME = 0.8
EFFECT_DISPLAY_TIME = 0.5

# MPV window detection
MPV_WINDOW_CLASS = "mpv"
X_DISPLAY = ":0"
