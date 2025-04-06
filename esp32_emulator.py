import pygame
import socket
import json
import threading
import time

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

# Odwrotne mapowanie
CHESS_TO_LED = {v: k for k, v in LED_TO_CHESS.items()}

# Mapowanie pinów MCP23017 na numery LED
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

# Mapowanie LED na piny MCP
LED_TO_MCP_PIN = {}
for mcp_name, ports in MAPPING.items():
    for port_name, pins in ports.items():
        for pin_name, led_num in pins.items():
            LED_TO_MCP_PIN[led_num] = (mcp_name, port_name, pin_name)

# Kolory RGB dla LED
COLOR_MAP = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
    "off": (50, 50, 50)
}


class ChessboardSimulator:
    def __init__(self, width=800, height=800, server_host='localhost', server_port=5000):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Symulator Szachownicy LED")

        self.cell_size = min(width, height) // 8
        self.server_host = server_host
        self.server_port = server_port

        # Stan przełączników Reeda
        self.reed_state = {
            mcp: {
                port: {pin: 0 for pin in pins}
                for port, pins in ports.items()
            }
            for mcp, ports in MAPPING.items()
        }

        # Stan LED: {led_num: {"state": 0/1, "color": "red"/"green"/"yellow"/"orange"}}
        self.led_state = {led: {"state": 0, "color": "off"} for led in LED_TO_CHESS.keys()}

        # Zmienne do kontroli wyświetlania komunikatów
        self.last_message = ""
        self.message_time = 0

        # Wątek komunikacji
        self.running = True
        self.thread = threading.Thread(target=self.simulate_esp32)
        self.thread.daemon = True
        self.thread.start()

    def draw_chessboard(self):
        self.screen.fill((255, 255, 255))

        for row in range(8):
            for col in range(8):
                x = col * self.cell_size
                y = (7 - row) * self.cell_size

                # Kolor pola
                color = (240, 217, 181) if (row + col) % 2 == 0 else (181, 136, 99)
                pygame.draw.rect(self.screen, color, (x, y, self.cell_size, self.cell_size))

                # Oznaczenia pól
                chess_pos = f"{chr(97 + col)}{row + 1}"
                font = pygame.font.SysFont('Arial', 14)

                # Czujnik Reeda (lewy dolny róg)
                led_num = CHESS_TO_LED.get(chess_pos)
                if led_num:
                    reed_state = self.get_reed_state(led_num)
                    reed_pos = (x + 10, y + self.cell_size - 10)
                    pygame.draw.circle(self.screen, (0, 255, 0) if reed_state else (100, 100, 100), reed_pos, 6)

                # LED (prawy górny róg)
                if led_num and led_num in self.led_state:
                    led_pos = (x + self.cell_size - 10, y + 10)
                    led_info = self.led_state[led_num]
                    led_color = COLOR_MAP[led_info["color"]] if led_info["state"] == 1 else COLOR_MAP["off"]
                    pygame.draw.circle(self.screen, led_color, led_pos, 8)

                # Etykiety
                text = font.render(chess_pos, True, (0, 0, 0))
                self.screen.blit(text, (x + 5, y + 5))
                if led_num:
                    led_text = font.render(str(led_num), True, (0, 0, 0))
                    self.screen.blit(led_text, (x + self.cell_size - 25, y + self.cell_size - 20))

        # Legenda
        font = pygame.font.SysFont('Arial', 16)
        legends = [
            ("Zielony LED: figura na linii startowej", COLOR_MAP["green"]),
            ("Czerwony LED: figura na niedozwolonym polu", COLOR_MAP["red"]),
            ("Żółty/Pomarańczowy LED: brak figury na linii startowej", COLOR_MAP["yellow"]),
            ("Zielony krąg: aktywny czujnik Reed", (0, 255, 0))
        ]

        for i, (text, color) in enumerate(legends):
            y_pos = self.height - 80 + i * 20
            pygame.draw.circle(self.screen, color, (15, y_pos), 6)
            self.screen.blit(font.render(text, True, (0, 0, 0)), (30, y_pos - 8))

        pygame.display.flip()

    def get_reed_state(self, led_num):
        if led_num in LED_TO_MCP_PIN:
            mcp, port, pin = LED_TO_MCP_PIN[led_num]
            return self.reed_state[mcp][port][pin]
        return 0

    def handle_click(self, pos):
        x, y = pos
        col = x // self.cell_size
        row = 7 - (y // self.cell_size)

        if 0 <= row < 8 and 0 <= col < 8:
            chess_pos = f"{chr(97 + col)}{row + 1}"
            led_num = CHESS_TO_LED.get(chess_pos)

            if led_num and led_num in LED_TO_MCP_PIN:
                mcp, port, pin = LED_TO_MCP_PIN[led_num]
                self.reed_state[mcp][port][pin] ^= 1  # Toggle stanu

    def check_board_status(self):
        """
        Sprawdza stan szachownicy i wyświetla odpowiednie komunikaty w konsoli.

        Zasady:
        1. "Ustaw figury na polach startowych!" - jeśli brakuje figur na liniach 1,2,7,8
        2. "Figura na błędnym polu!" - jeśli wykryto figury na liniach 3,4,5,6
        3. "Gotowe do gry!" - jeśli figury są tylko na liniach startowych i nie ma błędów
        """
        # Sprawdź czy wszystkie pola startowe mają figury
        starting_positions_ok = True
        for led_num, position in LED_TO_CHESS.items():
            rank = position[1]
            if rank in ['1', '2', '7', '8']:
                reed_state = self.get_reed_state(led_num)
                if reed_state == 0:  # Brak figury na polu startowym
                    starting_positions_ok = False
                    break

        # Sprawdź czy są figury na polach środkowych (niedozwolonych)
        illegal_positions = False
        illegal_positions_list = []
        for led_num, position in LED_TO_CHESS.items():
            rank = position[1]
            if rank in ['3', '4', '5', '6']:
                reed_state = self.get_reed_state(led_num)
                if reed_state == 1:  # Figura na niedozwolonym polu
                    illegal_positions = True
                    illegal_positions_list.append(position)

        # Wyświetl odpowiedni komunikat
        current_time = time.time()
        message = ""

        if illegal_positions:
            msg = f"Figura na błędnym polu! Niedozwolone pozycje: {', '.join(illegal_positions_list)}"
            if msg != self.last_message or current_time - self.message_time > 5:
                print(f"\033[91m{msg}\033[0m")  # Czerwony tekst
                self.last_message = msg
                self.message_time = current_time
        elif not starting_positions_ok:
            msg = "Ustaw figury na polach startowych!"
            if msg != self.last_message or current_time - self.message_time > 5:
                print(f"\033[93m{msg}\033[0m")  # Żółty tekst
                self.last_message = msg
                self.message_time = current_time
        else:
            msg = "Gotowe do gry!"
            if msg != self.last_message or current_time - self.message_time > 5:
                print(f"\033[92m{msg}\033[0m")  # Zielony tekst
                self.last_message = msg
                self.message_time = current_time

    def simulate_esp32(self):
        while self.running:
            try:
                with socket.socket() as s:
                    s.connect((self.server_host, self.server_port))
                    s.sendall(json.dumps(self.reed_state).encode())

                    response = json.loads(s.recv(4096).decode())

                    # Resetuj stan wszystkich LED
                    for led in self.led_state:
                        self.led_state[led] = {"state": 0, "color": "off"}

                    # Aktualizuj stan LED na podstawie otrzymanych danych
                    for led_info in response.get('leds', []):
                        led_num = led_info['led']
                        if led_num in self.led_state:
                            self.led_state[led_num] = {"state": 1, "color": led_info['color']}

                    # Sprawdź i wyświetl komunikaty o stanie szachownicy
                    self.check_board_status()

            except Exception as e:
                print(f"Błąd połączenia: {e}")
            time.sleep(0.1)

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            self.draw_chessboard()
            clock.tick(30)


if __name__ == "__main__":
    simulator = ChessboardSimulator()
    simulator.run()
