# config.py
# Mapowanie pinów MCP na numery LED
MAPPING = {
    "MCP1": {
        "PA": {"PA7": 15, "PA6": 13, "PA5": 11, "PA4": 9, "PA3": 7, "PA2": 5, "PA1": 3, "PA0": 1},
        "PB": {"PB7": 16, "PB6": 18, "PB5": 20, "PB4": 22, "PB3": 24, "PB2": 26, "PB1": 28, "PB0": 30}
    },
    "MCP2": {
        "PA": {"PA7": 45, "PA6": 43, "PA5": 41, "PA4": 39, "PA3": 37, "PA2": 35, "PA1": 33, "PA0": 31},
        "PB": {"PB7": 46, "PB6": 48, "PB5": 50, "PB4": 52, "PB3": 54, "PB2": 56, "PB1": 58, "PB0": 60}
    },
    "MCP3": {
        "PA": {"PA7": 75, "PA6": 73, "PA5": 71, "PA4": 69, "PA3": 67, "PA2": 65, "PA1": 63, "PA0": 61},
        "PB": {"PB7": 76, "PB6": 78, "PB5": 80, "PB4": 82, "PB3": 84, "PB2": 86, "PB1": 88, "PB0": 90}
    },
    "MCP4": {
        "PA": {"PA7": 105, "PA6": 103, "PA5": 101, "PA4": 99, "PA3": 97, "PA2": 95, "PA1": 93, "PA0": 91},
        "PB": {"PB7": 106, "PB6": 108, "PB5": 110, "PB4": 112, "PB3": 114, "PB2": 116, "PB1": 118, "PB0": 120}
    }
}

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

# Odwrotne mapowanie - z pola szachownicy na numer LED
CHESS_TO_LED = {v: k for k, v in LED_TO_CHESS.items()}

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
LICHESS_API_TOKEN = "xxx"  # Wpisz swój token API