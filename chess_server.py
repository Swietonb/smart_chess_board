# chess_server.py
import socket
import json
import threading
from config import SERVER_HOST, SERVER_PORT, BUFFER_SIZE
from chess_logic import process_data, is_board_ready


class ChessServer:
    def __init__(self, host=SERVER_HOST, port=SERVER_PORT, on_board_ready=None):
        """Inicjalizacja serwera szachownicy."""
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.on_board_ready_callback = on_board_ready
        self.board_ready = False
        self.last_board_ready_state = False

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
            data = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if not data:
                return

            # Parsujemy dane JSON
            reed_data = json.loads(data)

            # Zachowaj kopię reed_data do zwrócenia
            original_reed_data = reed_data.copy()

            # Przetwarzamy dane i ustalamy, które LED zapalić i w jakim kolorze
            leds_with_colors = process_data(reed_data)

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
