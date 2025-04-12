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

        self.game_mode = False

        # Stan pulsacji dla migających diod
        self.pulse_state = False
        self.last_pulse_change = time.time()

        # Dodane pola do wyświetlania statusu
        self.is_player_turn = False
        self.opponent_move_pending = False

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
            self.server_socket.listen(1)  # Przyjmuj tylko jedno połączenie na raz
            print(f"Serwer uruchomiony na {self.host}:{self.port}")

            while self.running:
                print("Oczekiwanie na połączenie ESP32...")
                # Akceptuj połączenie bez timeout
                self.server_socket.settimeout(None)
                client_socket, client_address = self.server_socket.accept()
                print(f"Połączono z ESP32: {client_address}")

                # Obsługa klienta w tej samej pętli
                self._handle_client(client_socket)

        except KeyboardInterrupt:
            print("\nWyłączanie serwera...")
        except Exception as e:
            print(f"Błąd serwera: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

    def _handle_client(self, client_socket):
        """Obsługuje połączenie od klienta (ESP32) - model zdarzeniowy."""
        try:
            client_socket.settimeout(5.0)
            buffer = b""

            # Stan LED dla porównywania zmian
            previous_led_states = {}

            print(f"Połączono z ESP32: {client_socket.getpeername()}")

            while self.running:
                try:
                    # Odbierz dane od ESP32
                    data = client_socket.recv(self.BUFFER_SIZE)
                    if not data:
                        print("Klient rozłączony")
                        break

                    buffer += data

                    # Przetwarzaj tylko kompletne dane JSON
                    json_start = buffer.find(b'{')
                    if json_start >= 0:
                        # Zliczanie nawiasów do znalezienia końca JSON
                        open_braces = 0
                        json_end = -1

                        for i in range(json_start, len(buffer)):
                            if buffer[i] == ord('{'):
                                open_braces += 1
                            elif buffer[i] == ord('}'):
                                open_braces -= 1

                            if open_braces == 0:
                                json_end = i + 1
                                break

                        # Jeśli znaleziono kompletny JSON
                        if json_end > 0:
                            json_data = buffer[json_start:json_end]
                            buffer = buffer[json_end:]  # Zachowaj resztę danych

                            # Przetwarzanie kompletnego JSON
                            try:
                                data_str = json_data.decode('utf-8').strip()

                                message = json.loads(data_str)

                                # Sprawdź typ wiadomości i zdarzenie
                                event_type = "unknown"
                                if isinstance(message, dict):
                                    if message.get("type") == "reed_state":
                                        reed_data = message.get("data", {})
                                        event_type = message.get("event", "unknown")
                                    else:
                                        reed_data = message
                                else:
                                    reed_data = message

                                #print(f"Odebrano dane od ESP32 - zdarzenie: {event_type}")

                                # Zachowaj kopię danych
                                original_reed_data = reed_data.copy()

                                # Wykryj zmiany w przełącznikach Reed
                                reed_changes = None
                                if self.previous_reed_data:
                                    reed_changes = self._detect_reed_changes(self.previous_reed_data, reed_data)

                                # Aktualizuj poprzedni stan
                                self.previous_reed_data = reed_data.copy()

                                # Przygotuj listę LED do zapalenia
                                leds_with_colors = []

                                # Dodaj niestandardowe diody
                                custom_leds_positions = set()
                                if hasattr(self, 'custom_leds') and self.custom_leds:
                                    for custom_led in self.custom_leds.copy():
                                        led_num = custom_led["led"]
                                        color = custom_led["color"]
                                        blink = custom_led.get("blink", False)

                                        leds_with_colors.append({
                                            "led": led_num,
                                            "color": color,
                                            "blink": blink
                                        })
                                        custom_leds_positions.add(led_num)

                                # Dodaj standardowe podświetlenia w trybie ustawiania
                                if not hasattr(self, 'game_mode') or not self.game_mode:
                                    standard_leds = process_data(reed_data)
                                    for led_info in standard_leds:
                                        if led_info["led"] not in custom_leds_positions:
                                            leds_with_colors.append(led_info)

                                # Sprawdź czy szachownica jest gotowa
                                was_ready = self.board_ready
                                self.board_ready = is_board_ready(reed_data)

                                # Jeśli stan gotowości się zmienił, wywołaj callback
                                if self.board_ready and not was_ready and self.on_board_ready_callback:
                                    self.custom_leds = []  # Wyczyść niestandardowe diody

                                    # Wyślij natychmiastową aktualizację do ESP32
                                    response = json.dumps({
                                        "leds": [],
                                        "status": "Szachownica gotowa. Podaj ID partii."
                                    })
                                    client_socket.sendall(response.encode() + b'\n')
                                    self.on_board_ready_callback()

                                # Przygotuj status gry
                                game_status = "Ustaw figury w pozycji startowej"
                                if self.board_ready:
                                    if hasattr(self, 'game_mode') and self.game_mode:
                                        if hasattr(self, 'is_player_turn') and self.is_player_turn:
                                            game_status = "Twoj ruch! Podnieś figurę, którą chcesz ruszyć."
                                        else:
                                            if hasattr(self, 'opponent_move_pending') and self.opponent_move_pending:
                                                game_status = "Wykonaj ruch przeciwnika na szachownicy."
                                            else:
                                                game_status = "Oczekiwanie na ruch przeciwnika..."
                                    else:
                                        game_status = "Szachownica gotowa. Podaj ID partii."

                                # Określ, czy trzeba wysłać odpowiedź na podstawie zdarzenia
                                send_response = False

                                if event_type == "unknown":
                                    send_response = True

                                # 1. Heartbeat - zawsze odpowiadaj aby potwierdzić połączenie
                                if event_type == "heartbeat":
                                    send_response = True

                                # 2. Zmiana fazy gry - zawsze odpowiadaj
                                elif event_type == "phase_change":
                                    send_response = True

                                # 3. Zmiana stanu Reed - odpowiadaj w zależności od fazy gry
                                elif event_type == "reed_change":
                                    # W trybie gry
                                    if hasattr(self, 'game_mode') and self.game_mode:
                                        # Jeśli jest tura gracza - zawsze odpowiadaj na zmiany Reed
                                        if hasattr(self, 'is_player_turn') and self.is_player_turn:
                                            send_response = True
                                            print("Wykryto ruch gracza w jego turze - wysyłam odpowiedź")
                                        # Jeśli wykonujemy ruch przeciwnika - też odpowiadaj
                                        elif hasattr(self, 'opponent_move_pending') and self.opponent_move_pending:
                                            send_response = True
                                            print(
                                                "Wykryto zmianę podczas wykonywania ruchu przeciwnika - wysyłam odpowiedź")
                                    else:
                                        # W trybie ustawiania - odpowiadaj na zmiany Reed
                                        send_response = True

                                # Sprawdź, czy stan LED się zmienił
                                current_led_states = {}
                                for led_info in leds_with_colors:
                                    led_num = led_info["led"]
                                    led_key = f"{led_num}:{led_info['color']}:{led_info.get('blink', False)}"
                                    current_led_states[led_num] = led_key

                                led_state_changed = (previous_led_states != current_led_states)

                                # Wyślij odpowiedź jeśli:
                                # - Zdarzenie wymaga odpowiedzi
                                # - Stan LED się zmienił
                                # - To pierwsza odpowiedź
                                if send_response or led_state_changed or not previous_led_states:
                                    previous_led_states = current_led_states.copy()

                                    response = json.dumps({
                                        "leds": leds_with_colors,
                                        "status": game_status
                                    })
                                    client_socket.sendall(response.encode() + b'\n')

                                    #print(f"Wysłano odpowiedź na zdarzenie: {event_type}")

                            except json.JSONDecodeError as e:
                                print(f"Błąd parsowania JSON: {e}")
                                print(f"Dane: '{data_str}'")

                except socket.timeout:
                    # Timeout jest OK
                    continue
                except ConnectionResetError:
                    print("Połączenie resetowane przez ESP32")
                    break
                except Exception as e:
                    print(f"Błąd podczas obsługi połączenia: {e}")
                    break

        except Exception as e:
            print(f"Błąd obsługi klienta: {e}")
        finally:
            client_socket.close()
            print("Połączenie z ESP32 zakończone")

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
