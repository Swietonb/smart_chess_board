import pygame
import socket
import json
import threading
import time

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
