# -*- coding: utf-8 -*-
"""Terminal theme detection and color utilities."""

import os
import sys
import select
import time
import re
from typing import Tuple, List, Optional

class Theme:
    def __init__(
        self,
        name: str,
        accent_blue: Tuple[int, int, int],
        accent_purple: Tuple[int, int, int],
        accent_green: Tuple[int, int, int],
        accent_yellow: Tuple[int, int, int],
        accent_red: Tuple[int, int, int],
        gray: Tuple[int, int, int],
        gradient_stops: List[Tuple[int, int, int]]
    ):
        self.name = name
        self.accent_blue = accent_blue
        self.accent_purple = accent_purple
        self.accent_green = accent_green
        self.accent_yellow = accent_yellow
        self.accent_red = accent_red
        self.gray = gray
        self.gradient_stops = gradient_stops

DARK_THEME = Theme(
    name="dark",
    accent_blue=(137, 180, 250),    # #89B4FA
    accent_purple=(203, 166, 247),  # #CBA6F7
    accent_green=(166, 227, 161),   # #A6E3A1
    accent_yellow=(249, 226, 175),  # #F9E2AF
    accent_red=(243, 139, 168),     # #F38BA8
    gray=(108, 112, 134),           # #6C7086
    gradient_stops=[(71, 150, 228), (132, 122, 206), (195, 103, 127)] # #4796E4, #847ACE, #C3677F
)

LIGHT_THEME = Theme(
    name="light",
    accent_blue=(59, 130, 246),     # #3B82F6
    accent_purple=(139, 92, 246),   # #8B5CF6
    accent_green=(60, 168, 75),     # #3CA84B
    accent_yellow=(213, 164, 10),   # #D5A40A
    accent_red=(221, 76, 76),       # #DD4C4C
    gray=(151, 160, 176),           # #97a0b0
    gradient_stops=[(71, 150, 228), (132, 122, 206), (195, 103, 127)]
)

_cached_is_dark: Optional[bool] = None

def get_luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculates relative luminance (0-255)."""
    def adjust(c):
        c /= 255.0
        if c <= 0.03928:
            return c / 12.92
        else:
            return ((c + 0.055) / 1.055) ** 2.4
    
    r = adjust(rgb[0])
    g = adjust(rgb[1])
    b = adjust(rgb[2])
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) * 255

def get_terminal_background_color_osc() -> Optional[str]:
    """Queries the terminal for its background color using OSC 11 and a sentinel."""
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return None

    if os.name == 'nt':
        return None

    try:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            
            # 1. Flush input buffer
            termios.tcflush(fd, termios.TCIFLUSH)
            
            # 2. Queries (Matching TS version logic)
            query = "\033[8m\033]11;?\033\\\033[c\033[2K\r\033[0m"
            sys.stdout.write(query)
            sys.stdout.flush()

            response = ""
            bg_response = ""
            start_time = time.time()
            
            # 3. Read loop (up to 0.5s)
            while time.time() - start_time < 0.5:
                rlist, _, _ = select.select([fd], [], [], 0.05)
                if rlist:
                    # Use os.read for unbuffered raw access
                    chunk_bytes = os.read(fd, 4096)
                    if not chunk_bytes:
                        break
                    chunk = chunk_bytes.decode('utf-8', errors='ignore')
                    response += chunk
                    
                    # Check for Ctrl+C (\x03) manually since we're in raw mode
                    if "\x03" in response:
                        raise KeyboardInterrupt()
                    
                    # Check for OSC 11 response
                    osc_match = re.search(r"\033\]11;rgb:[0-9a-fA-F/]+(\007|\033\\)", response)
                    if osc_match:
                        bg_response = osc_match.group(0)
                    
                    # Sentinel check: Device Attributes response
                    if re.search(r"\033\[\??[\d;]*c", response):
                        break
            
            return bg_response if bg_response else None
        finally:
            # Restore settings immediately using TCSANOW
            termios.tcsetattr(fd, termios.TCSANOW, old_settings)
    except KeyboardInterrupt:
        # Re-raise to allow app to exit
        raise
    except Exception:
        return None

def parse_osc_response(response: str) -> Optional[Tuple[int, int, int]]:
    """Parses OSC 11 response like \033]11;rgb:rrrr/gggg/bbbb\007 or \033]11;rgb:rrrr/gggg/bbbb\033\\"""
    # Matches 1-4 hex digits per channel
    pattern = r"rgb:([0-9a-fA-F]{1,4})/([0-9a-fA-F]{1,4})/([0-9a-fA-F]{1,4})"
    match = re.search(pattern, response)
    if not match:
        return None
    
    try:
        def hex_to_int(h):
            val = int(h, 16)
            if len(h) == 1: return int((val / 15) * 255)
            if len(h) == 2: return val
            if len(h) == 3: return int((val / 4095) * 255)
            if len(h) == 4: return int((val / 65535) * 255)
            return val
        
        return (hex_to_int(match.group(1)), hex_to_int(match.group(2)), hex_to_int(match.group(3)))
    except Exception:
        pass
    return None

def is_dark_mode() -> bool:
    """Determines if the terminal is in dark mode."""
    global _cached_is_dark
    if _cached_is_dark is not None:
        return _cached_is_dark

    # 1. Try OSC query
    resp = get_terminal_background_color_osc()
    if resp:
        rgb = parse_osc_response(resp)
        if rgb:
            _cached_is_dark = get_luminance(rgb) <= 128
            return _cached_is_dark
    
    # 2. Fallback to COLORFGBG environment variable
    colorfgbg = os.environ.get("COLORFGBG")
    if colorfgbg and ";" in colorfgbg:
        try:
            bg = int(colorfgbg.split(";")[-1])
            # Simple heuristic for 16-color palette
            if bg in [0, 1, 2, 3, 4, 5, 6, 8]:
                _cached_is_dark = True
                return True
            if bg in [7, 10, 11, 12, 13, 14, 15]:
                _cached_is_dark = False
                return False
        except ValueError:
            pass
            
    # 3. Default to light
    _cached_is_dark = False
    return False

def get_theme() -> Theme:
    """Returns the appropriate theme based on terminal background."""
    if is_dark_mode():
        return DARK_THEME
    return LIGHT_THEME
