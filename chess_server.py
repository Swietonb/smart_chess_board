# chess_server.py
import socket
import json
import threading
from config import SERVER_HOST, SERVER_PORT, BUFFER_SIZE
from chess_logic import process_data, is_board_ready
import time

class ChessServer:
    def __init__(self, host=SERVER_HOST, port=SERVER_PORT, on_board_ready=None, on_reed_change=None):
        """Inicjalizacja serwera szachownicy."""
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.on_board_ready_callback = on_board_ready
        self.on_reed_change_callback = on_reed_change
        self.board_ready = False
        self.last_board_ready_state = False
        self.custom_leds = []
        self.previous_reed_data = None

        # Dodaj flagę trybu gry - na początku jest False (tryb ustawiania figur)
        self.game_mode = False

        # Stan pulsacji dla migających diod
        self.pulse_state = False
        self.last_pulse_change = time.time()

    def start(self):
        """Uruchamia serwer w osobnym wątku."""
        self.running = True
        server_thread = threading.Thread(target=self._run_server)
        server_thread.daemon = True
        server_thread.start()
        return server_thread

    def stop(self):
        """Zatrzymuje serwer."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

    def set_game_mode(self, enabled=True):
        """Włącza lub wyłącza tryb gry."""
        self.game_mode = enabled
        print(f"DEBUG: Tryb gry {'włączony' if enabled else 'wyłączony'}")

    def _run_server(self):
        """Uruchamia serwer w wątku."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)

            print(f"Serwer uruchomiony na {self.host}:{self.port}")

            while self.running:
                try:
                    # Timeout aby móc bezpieczniej zakończyć serwer
                    self.server_socket.settimeout(1.0)
                    client_socket, client_address = self.server_socket.accept()

                    # Obsługa klienta w osobnym wątku
                    client_thread = threading.Thread(target=self._handle_client, args=(client_socket,))
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:  # Ignoruj błędy podczas zamykania
                        print(f"Błąd serwera: {e}")

        except KeyboardInterrupt:
            print("\nWyłączanie serwera...")
        except Exception as e:
            print(f"Błąd serwera: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

    def _handle_client(self, client_socket):
        """Obsługuje połączenie od klienta (ESP32)."""
        try:
            # Odbieramy dane z ESP32
            data = client_socket.recv(self.BUFFER_SIZE).decode('utf-8')
            if not data:
                return

            # Parsujemy dane JSON
            reed_data = json.loads(data)

            # Zachowaj kopię reed_data do zwrócenia
            original_reed_data = reed_data.copy()

            # Wykryj zmiany w stanach przełączników Reed
            if self.previous_reed_data:
                self._detect_reed_changes(self.previous_reed_data, reed_data)

            # Zapamiętaj obecny stan Reed
            self.previous_reed_data = reed_data.copy()

            # Aktualizacja stanu pulsacji co 0.5 sekundy
            current_time = time.time()
            if current_time - self.last_pulse_change > 0.5:
                self.pulse_state = not self.pulse_state
                self.last_pulse_change = current_time

            # Przygotuj listę LED z informacją o kolorze
            leds_with_colors = []

            # PRIORYTET 1: Najpierw dodaj niestandardowe diody (własne podświetlenia pól)
            custom_leds_positions = set()
            if self.custom_leds:
                for custom_led in self.custom_leds.copy():  # Używamy kopii, aby bezpiecznie modyfikować
                    led_num = custom_led["led"]
                    color = custom_led["color"]
                    blink = custom_led.get("blink", False)

                    # Jeśli dioda ma migać, obsłuż to
                    if blink:
                        if self.pulse_state:
                            leds_with_colors.append({"led": led_num, "color": color})
                    else:
                        leds_with_colors.append({"led": led_num, "color": color})

                    custom_leds_positions.add(led_num)

            # PRIORYTET 2: Dodaj standardowe podświetlenia tylko w trybie ustawiania figur
            if not self.game_mode:
                standard_leds = process_data(reed_data)
                for led_info in standard_leds:
                    if led_info["led"] not in custom_leds_positions:
                        leds_with_colors.append(led_info)

            # Sprawdź czy szachownica jest gotowa NA PODSTAWIE STANU REED
            was_ready = self.board_ready
            self.board_ready = is_board_ready(reed_data)

            # Jeśli stan gotowości się zmienił, wywołaj callback
            if self.board_ready and not was_ready and self.on_board_ready_callback:
                self.on_board_ready_callback()

            # Odsyłamy informacje o LED do ESP32 wraz ze stanem reed switchy
            response = json.dumps({
                "leds": leds_with_colors,
                "reed_state": original_reed_data
            })
            client_socket.sendall(response.encode('utf-8'))

        except Exception as e:
            print(f"Błąd obsługi klienta: {e}")
        finally:
            client_socket.close()
    def _detect_reed_changes(self, previous_data, current_data):
        """Wykrywa zmiany w stanach przełączników Reed i obsługuje je."""
        changes = []

        # Porównaj poprzedni i obecny stan Reed
        for mcp_name, ports in current_data.items():
            for port_name, pins in ports.items():
                for pin_name, current_state in pins.items():
                    # Pobierz poprzedni stan pinu
                    previous_state = previous_data.get(mcp_name, {}).get(port_name, {}).get(pin_name, 0)

                    # Jeśli stan się zmienił
                    if current_state != previous_state:
                        # Pobierz numer LED i pozycję szachową
                        led_num = self.MAPPING[mcp_name][port_name][pin_name]
                        chess_pos = self.LED_TO_CHESS.get(led_num)

                        if chess_pos:
                            # Dodaj informację o zmianie
                            changes.append({
                                "position": chess_pos,
                                "from_state": previous_state,
                                "to_state": current_state
                            })

        # Jeśli wykryto zmiany, obsłuż je
        if changes and self.on_reed_change_callback:
            self.on_reed_change_callback(changes)

    def set_led(self, position, color, blink=False):
        """Ustawia diodę LED na określonej pozycji."""
        if not hasattr(self, 'custom_leds'):
            self.custom_leds = []

        # Sprawdź czy pozycja jest prawidłowa
        if position in self.CHESS_TO_LED:
            led_num = self.CHESS_TO_LED[position]

            # Sprawdź czy ta dioda już jest na liście
            for i, led in enumerate(self.custom_leds):
                if led.get("led") == led_num:
                    # Aktualizuj istniejącą diodę
                    self.custom_leds[i] = {"led": led_num, "color": color, "blink": blink}
                    return

            # Dodaj nową diodę
            self.custom_leds.append({"led": led_num, "color": color, "blink": blink})

    def clear_led(self, position):
        """Usuwa diodę LED z określonej pozycji."""
        if not hasattr(self, 'custom_leds'):
            return

        if position in self.CHESS_TO_LED:
            led_num = self.CHESS_TO_LED[position]

            # Usuń diodę z listy
            self.custom_leds = [led for led in self.custom_leds if led.get("led") != led_num]

    def clear_all_leds(self):
        """Usuwa wszystkie niestandardowe diody LED."""
        self.custom_leds = []