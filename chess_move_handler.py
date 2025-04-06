import threading
import time
from config import COLOR_GREEN, COLOR_RED, COLOR_YELLOW, COLOR_ORANGE


class ChessMoveHandler:
    def __init__(self, chess_server, lichess_client):
        """Inicjalizuje obsługę ruchów szachowych."""
        self.chess_server = chess_server
        self.lichess_client = lichess_client

        # Stan ruchu
        self.move_in_progress = False
        self.source_position = None
        self.timer = None
        self.is_player_turn = False

    def set_player_turn(self, is_turn):
        """Ustawia, czy jest tura gracza."""
        self.is_player_turn = is_turn

    def handle_reed_change(self, changes):
        """Obsługuje zmiany stanu przełączników Reed."""
        if not self.is_player_turn:
            # Jeśli nie jest tura gracza, ignoruj zmiany
            print("DEBUG: Zmiany zignorowane - nie jest tura gracza")
            return

        for change in changes:
            position = change["position"]
            from_state = change["from_state"]
            to_state = change["to_state"]

            print(f"DEBUG: Wykryto zmianę na {position}: {from_state} -> {to_state}")

            # Podniesienie figury (Reed z 1 na 0)
            if from_state == 1 and to_state == 0:
                self._handle_figure_lifted(position)

            # Postawienie figury (Reed z 0 na 1)
            elif from_state == 0 and to_state == 1:
                self._handle_figure_placed(position)

    def _handle_figure_lifted(self, position):
        """Obsługuje podniesienie figury."""
        # Jeśli już jest ruch w trakcie, ignoruj
        if self.move_in_progress and self.source_position:
            return

        print(f"Podniesiono figurę z pola {position}")

        # Wyczyść wszystkie diody z poprzednich ruchów
        self.chess_server.clear_all_leds()

        # Rozpocznij nowy ruch
        self.move_in_progress = True
        self.source_position = position

        # Zapal diodę na pozycji źródłowej (migająca zielona)
        self.chess_server.set_led(position, COLOR_GREEN, blink=True)

    def _handle_figure_placed(self, position):
        """Obsługuje postawienie figury."""
        # Jeśli nie ma ruchu w trakcie lub nie ma pozycji źródłowej, ignoruj
        if not self.move_in_progress or not self.source_position:
            return

        # Jeśli pozycja docelowa jest taka sama jak źródłowa, ignoruj
        if position == self.source_position:
            return

        print(f"Postawiono figurę na polu {position}")

        # Pozycja docelowa
        target_position = position

        # Zapal diodę na pozycji docelowej (migająca zielona)
        self.chess_server.set_led(target_position, COLOR_GREEN, blink=True)

        # Uruchom timer na sekundę przed wykonaniem ruchu
        if self.timer:
            self.timer.cancel()

        print(f"Potwierdzanie ruchu z {self.source_position} na {target_position}. Czekaj 1 sekundę...")
        self.timer = threading.Timer(1.0, self._execute_move, args=[self.source_position, target_position])
        self.timer.start()

    def _execute_move(self, source, target):
        """Wykonuje ruch po upływie czasu potwierdzenia."""
        # Stwórz notację UCI (np. "e2e4")
        uci_move = f"{source}{target}"

        print(f"Wykonuję ruch: {uci_move}")

        # Wykonaj ruch w API Lichess
        success = self.lichess_client.make_move(uci_move)

        # Wyczyść wszystkie diody
        self.chess_server.clear_all_leds()

        # Zresetuj stan ruchu
        self.move_in_progress = False
        self.source_position = None

        # Wyłącz turę gracza po wykonaniu ruchu
        if success:
            self.is_player_turn = False
        else:
            print(f"Błąd podczas wykonywania ruchu {uci_move}. Spróbuj ponownie.")

    def stop(self):
        """Zatrzymuje obsługę ruchów."""
        if self.timer:
            self.timer.cancel()
