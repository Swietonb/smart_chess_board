# config.py
# Mapowanie pinów MCP na numery LED
MAPPING = {
    "MCP1": {
        "PA": {"PA7": 16, "PA6": 18, "PA5": 20, "PA4": 22, "PA3": 24, "PA2": 26, "PA1": 28, "PA0": 30},
        "PB": {"PB7": 1, "PB6": 3, "PB5": 5, "PB4": 7, "PB3": 9, "PB2": 11, "PB1": 13, "PB0": 15}
    },
    "MCP2": {
        "PA": {"PA7": 46, "PA6": 48, "PA5": 50, "PA4": 52, "PA3": 54, "PA2": 56, "PA1": 58, "PA0": 60},
        "PB": {"PB7": 31, "PB6": 33, "PB5": 35, "PB4": 37, "PB3": 39, "PB2": 41, "PB1": 43, "PB0": 45}
    },
    "MCP3": {
        "PA": {"PA7": 76, "PA6": 78, "PA5": 80, "PA4": 82, "PA3": 84, "PA2": 86, "PA1": 88, "PA0": 90},
        "PB": {"PB7": 61, "PB6": 63, "PB5": 65, "PB4": 67, "PB3": 69, "PB2": 71, "PB1": 73, "PB0": 75}
    },
    "MCP4": {
        "PA": {"PA7": 106, "PA6": 108, "PA5": 110, "PA4": 112, "PA3": 114, "PA2": 116, "PA1": 118, "PA0": 120},
        "PB": {"PB7": 91, "PB6": 93, "PB5": 95, "PB4": 97, "PB3": 99, "PB2": 101, "PB1": 103, "PB0": 105}
    }
}
# Mapowanie numerów LED na pola szachownicy
# Mapowanie numerów LED na pola szachownicy
LED_TO_CHESS = {
    1: "a1", 3: "b1", 5: "c1", 7: "d1", 9: "e1", 11: "f1", 13: "g1", 15: "h1",
    16: "h2", 18: "g2", 20: "f2", 22: "e2", 24: "d2", 26: "c2", 28: "b2", 30: "a2",
    31: "a3", 33: "b3", 35: "c3", 37: "d3", 39: "e3", 41: "f3", 43: "g3", 45: "h3",
    46: "h4", 48: "g4", 50: "f4", 52: "e4", 54: "d4", 56: "c4", 58: "b4", 60: "a4",
    61: "a5", 63: "b5", 65: "c5", 67: "d5", 69: "e5", 71: "f5", 73: "g5", 75: "h5",
    76: "h6", 78: "g6", 80: "f6", 82: "e6", 84: "d6", 86: "c6", 88: "b6", 90: "a6",
    91: "a7", 93: "b7", 95: "c7", 97: "d7", 99: "e7", 101: "f7", 103: "g7", 105: "h7",
    106: "h8", 108: "g8", 110: "f8", 112: "e8", 114: "d8", 116: "c8", 118: "b8", 120: "a8"
}

CHESS_TO_LED = {
    "a1": 1, "b1": 3, "c1": 5, "d1": 7, "e1": 9, "f1": 11, "g1": 13, "h1": 15,
    "a2": 30, "b2": 28, "c2": 26, "d2": 24, "e2": 22, "f2": 20, "g2": 18, "h2": 16,
    "a3": 31, "b3": 33, "c3": 35, "d3": 37, "e3": 39, "f3": 41, "g3": 43, "h3": 45,
    "a4": 60, "b4": 58, "c4": 56, "d4": 54, "e4": 52, "f4": 50, "g4": 48, "h4": 46,
    "a5": 61, "b5": 63, "c5": 65, "d5": 67, "e5": 69, "f5": 71, "g5": 73, "h5": 75,
    "a6": 90, "b6": 88, "c6": 86, "d6": 84, "e6": 82, "f6": 80, "g6": 78, "h6": 76,
    "a7": 91, "b7": 93, "c7": 95, "d7": 97, "e7": 99, "f7": 101, "g7": 103, "h7": 105,
    "a8": 120, "b8": 118, "c8": 116, "d8": 114, "e8": 112, "f8": 110, "g8": 108, "h8": 106
}

# Kolory LED
COLOR_RED = "red"
COLOR_GREEN = "green"
COLOR_YELLOW = "yellow"
COLOR_ORANGE = "orange"

# Ustawienia serwera
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000
BUFFER_SIZE = 4096

# Konfiguracja Lichess API
LICHESS_API_TOKEN = "lip_tzSCoXqDGuuLpO4NvE2b"  # Wpisz swój token API