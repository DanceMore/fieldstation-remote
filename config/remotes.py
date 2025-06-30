#!/usr/bin/env python3
"""
Remote control protocol mappings for IR Remote Mapper
"""

# Remote control configurations with protocol mappings
REMOTE_CONFIGS = {
    "nec_0x32": {
        "protocol": "NEC",
        "address": "0x32",
        "mappings": {
            # Channel controls
            "0x11": "CHANNEL_UP",
            "0x14": "CHANNEL_DOWN",
            
            # Effects
            "0x10": "EFFECT_PREV",
            "0x12": "EFFECT_NEXT",
            
            # Digits
            "0x00": "DIGIT_0",
            "0x01": "DIGIT_1",
            "0x02": "DIGIT_2",
            "0x03": "DIGIT_3",
            "0x04": "DIGIT_4",
            "0x05": "DIGIT_5",
            "0x06": "DIGIT_6",
            "0x07": "DIGIT_7",
            "0x08": "DIGIT_8",
            "0x09": "DIGIT_9",
            
            # Commented out - volume/control mappings for future use
            # "0x15": "VOLUME_UP",
            # "0x16": "VOLUME_DOWN", 
            # "0x17": "MUTE",
            # "0x18": "POWER",
            # "0x19": "PAUSE",
            # "0x1A": "INFO",
            # "0x1B": "MENU",
            # "0x1C": "OK",
            # "0x1D": "BACK",
        }
    },
    
    "samsung_tv": {
        "protocol": "Samsung32",
        "address": "0x07",
        "mappings": {
            "0x12": "CHANNEL_UP",
            "0x10": "CHANNEL_DOWN",
            
            # Samsung digit mappings
            "0x04": "DIGIT_1",
            "0x05": "DIGIT_2", 
            "0x06": "DIGIT_3",
            "0x08": "DIGIT_4",
            "0x09": "DIGIT_5",
            "0x0A": "DIGIT_6",
            "0x0C": "DIGIT_7",
            "0x0D": "DIGIT_8",
            "0x0E": "DIGIT_9",
            "0x11": "DIGIT_0",
            
            # Commented out - additional Samsung mappings
            # "0x07": "VOLUME_UP",
            # "0x0B": "VOLUME_DOWN",
            # "0x0F": "MUTE", 
            # "0x02": "POWER",
        }
    },
    
    "sony": {
        "protocol": "SIRC",
        "address": "0x01",
        "mappings": {
            "0x10": "CHANNEL_UP",
            "0x11": "CHANNEL_DOWN",
            "0x33": "EFFECT_NEXT",
            "0x34": "EFFECT_PREV",
            
            # Sony digit mappings
            "0x00": "DIGIT_1",
            "0x01": "DIGIT_2",
            "0x02": "DIGIT_3", 
            "0x03": "DIGIT_4",
            "0x04": "DIGIT_5",
            "0x05": "DIGIT_6",
            "0x06": "DIGIT_7",
            "0x07": "DIGIT_8",
            "0x08": "DIGIT_9",
            "0x09": "DIGIT_0",
            
            # Commented out - additional Sony mappings
            # "0x12": "VOLUME_UP",
            # "0x13": "VOLUME_DOWN",
            # "0x14": "MUTE",
            # "0x15": "POWER",
        }
    },
    
    "sony_0x77": {
        "protocol": "SIRC", 
        "address": "0x77",
        "mappings": {
            "0x0D": "DIGITAL_ANALOG",
        }
    },
}

def map_ir_signal(protocol, address, command):
    """
    Map IR signal to standardized event name
    
    Args:
        protocol: IR protocol (e.g., "NEC", "Samsung32", "SIRC")
        address: IR address code (e.g., "0x32")
        command: IR command code (e.g., "0x11")
        
    Returns:
        tuple: (event_name, protocol, address, command)
    """
    for remote_name, config in REMOTE_CONFIGS.items():
        if config["protocol"] == protocol and config["address"] == address:
            if command in config["mappings"]:
                return config["mappings"][command], protocol, address, command
            else:
                return f"UNMAPPED_{remote_name}_{command}", protocol, address, command
    
    return f"UNKNOWN_{protocol}_{address}_{command}", protocol, address, command
