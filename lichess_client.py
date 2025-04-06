# lichess_client.py
import berserk
import threading
import time
import datetime


class LichessClient:
    def __init__(self, api_token, on_opponent_move=None, on_my_turn=None):
        """Inicjalizacja klienta Lichess."""
        self.session = berserk.TokenSession(api_token)
        self.client = berserk.Client(session=self.session)
        self.game_id = None
        self.player_color = None
        self.account_id = None
        self.on_opponent_move = on_opponent_move
        self.on_my_turn = on_my_turn
        self.game_thread = None
        self.running = False

        # Pobierz informacje o koncie
        try:
            account_info = self.client.account.get()
            self.account_id = account_info['id']
        except Exception as e:
            print(f"Błąd podczas pobierania informacji o koncie: {e}")
            self.account_id = None

    def start_game(self, game_id):
        """Rozpoczęcie śledzenia i grania partii o podanym ID."""
        self.game_id = game_id
        self.running = True

        # Uruchom śledzenie gry w osobnym wątku
        self.game_thread = threading.Thread(target=self._stream_game)
        self.game_thread.daemon = True
        self.game_thread.start()

    def _stream_game(self):
        """Strumieniuje stan gry i obsługuje zdarzenia."""
        try:
            for event in self.client.board.stream_game_state(self.game_id):
                if not self.running:
                    break

                event_type = event.get('type')

                if event_type == 'gameFull':
                    # Początkowy stan gry
                    white_id = event.get('white', {}).get('id')
                    self.player_color = 'white' if white_id == self.account_id else 'black'
                    print(f"Grasz jako: {self.player_color}")

                    self._display_game_info(event)

                    # Pobierz aktualny stan
                    state = event.get('state', {})
                    self._process_state(state)

                elif event_type == 'gameState':
                    # Aktualizacja stanu gry
                    self._process_state(event)

                # Małe opóźnienie, aby zapobiec zbyt szybkim aktualizacjom
                time.sleep(0.1)

        except berserk.exceptions.ResponseError as e:
            if 'Board API' in str(e):
                print("\nBłąd: Ta partia nie może być obsługiwana przez Board API.")
                print("Przyczyną może być tempo gry (tylko Classical i Correspondence są obsługiwane)")
                print("lub inne ograniczenia (gra musi być publiczna, nie może być zakończona, itp.)")

                # Użyj alternatywnego API do śledzenia partii
                self._track_with_alternative_api()
            else:
                print(f"Wystąpił błąd API: {e}")
        except Exception as e:
            print(f"Wystąpił błąd podczas śledzenia gry: {e}")

    def _track_with_alternative_api(self):
        """Śledzi grę za pomocą alternatywnego API."""
        print("\nUżywam alternatywnego API do śledzenia partii.")

        last_moves = []

        while self.running:
            try:
                # Pobierz aktualny stan gry
                game = self.client.games.export(self.game_id)

                # Sprawdź, czy gra się zakończyła
                if game.get('status') != 'started':
                    print(f"\nPartia zakończona. Wynik: {game.get('status')}")
                    break

                # Pobierz ruchy
                moves_str = game.get('moves', '')
                current_moves = self._parse_moves(moves_str)

                # Znajdź nowe ruchy
                if len(current_moves) > len(last_moves):
                    # Wyświetl nowe ruchy
                    for i in range(len(last_moves), len(current_moves)):
                        move_number = i // 2 + 1
                        is_white = i % 2 == 0
                        move = current_moves[i]

                        self._display_move(move_number, is_white, move)

                        # Sprawdź, czy to ruch przeciwnika
                        is_opponent_move = (self.player_color == 'white' and not is_white) or \
                                           (self.player_color == 'black' and is_white)

                        if is_opponent_move and self.on_opponent_move:
                            self.on_opponent_move(move)

                    # Zaktualizuj listę ruchów
                    last_moves = current_moves.copy()

                # Sprawdź, czy teraz jest kolej gracza
                is_my_turn = (self.player_color == 'white' and len(current_moves) % 2 == 0) or \
                             (self.player_color == 'black' and len(current_moves) % 2 == 1)

                if is_my_turn and self.on_my_turn:
                    self.on_my_turn()

                # Odczekaj przed następnym sprawdzeniem
                time.sleep(2)

            except Exception as e:
                print(f"Wystąpił błąd podczas pobierania stanu gry: {e}")
                time.sleep(5)  # Czekaj dłużej w przypadku błędu

    def _process_state(self, state):
        """Przetwarza stan gry."""
        # Pobierz ruchy
        moves_str = state.get('moves', '')
        current_moves = self._parse_moves(moves_str)

        # Wyświetl nowe ruchy
        if hasattr(self, 'last_moves'):
            # Znajdź nowe ruchy
            if len(current_moves) > len(self.last_moves):
                for i in range(len(self.last_moves), len(current_moves)):
                    move_number = i // 2 + 1
                    is_white = i % 2 == 0
                    move = current_moves[i]

                    # Wyświetl ruch
                    white_time = state.get('wtime') if is_white else None
                    black_time = state.get('btime') if not is_white else None
                    self._display_move(move_number, is_white, move, white_time, black_time)

                    # Sprawdź, czy to ruch przeciwnika
                    is_opponent_move = (self.player_color == 'white' and not is_white) or \
                                       (self.player_color == 'black' and is_white)

                    if is_opponent_move and self.on_opponent_move:
                        self.on_opponent_move(move)
        else:
            # Pierwsza aktualizacja - wyświetl wszystkie ruchy
            for i, move in enumerate(current_moves):
                move_number = i // 2 + 1
                is_white = i % 2 == 0

                # Wyświetl ruch
                white_time = state.get('wtime') if i == len(current_moves) - 2 else None
                black_time = state.get('btime') if i == len(current_moves) - 1 else None
                self._display_move(move_number, is_white, move, white_time, black_time)

        # Zapamiętaj ruchy
        self.last_moves = current_moves.copy()

        # Sprawdź, czy teraz jest kolej gracza
        is_my_turn = (self.player_color == 'white' and len(current_moves) % 2 == 0) or \
                     (self.player_color == 'black' and len(current_moves) % 2 == 1)

        if is_my_turn and self.on_my_turn:
            self.on_my_turn()

        # Sprawdź, czy gra się zakończyła
        if state.get('status') != 'started':
            print(f"\nPartia zakończona. Wynik: {state.get('status')}")
            self.running = False

    def _display_game_info(self, game_data):
        """Wyświetla podstawowe informacje o partii."""
        white_info = game_data.get('white', {})
        black_info = game_data.get('black', {})

        white_player = white_info.get('name', white_info.get('id', 'Unknown'))
        black_player = black_info.get('name', black_info.get('id', 'Unknown'))

        print(f"\nPartia: {white_player} (Biały) vs {black_player} (Czarny)")

        if 'clock' in game_data:
            initial_time = game_data['clock'].get('initial', 0) // 1000
            increment = game_data['clock'].get('increment', 0)
            minutes = initial_time // 60
            seconds = initial_time % 60
            print(f"Tempo: {minutes}:{seconds:02d}+{increment}")

        print("\nŚledzenie i wykonywanie ruchów:")
        print("-" * 40)

    def _display_move(self, move_number, is_white, move, white_time=None, black_time=None):
        """Wyświetla pojedynczy ruch z informacją o czasie, jeśli dostępna."""
        time_str = ""

        if is_white and white_time is not None:
            time_str = f" ({self._format_time(white_time)})"
        elif not is_white and black_time is not None:
            time_str = f" ({self._format_time(black_time)})"

        if is_white:
            print(f"{move_number}. {move}{time_str}", end="  ")
        else:
            print(f"{move}{time_str}")

    def _format_time(self, milliseconds):
        """Formatuje czas w milisekundach do czytelnego ciągu."""
        if milliseconds is None:
            return ""

        try:
            if isinstance(milliseconds, datetime.datetime):
                return milliseconds.strftime("%M:%S")
            else:
                total_seconds = int(milliseconds) // 1000
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                return f"{minutes}:{seconds:02d}"
        except Exception:
            return f"?"

    def _parse_moves(self, moves_str):
        """Przetwarza ciąg ruchów na listę pojedynczych ruchów."""
        if not moves_str or not isinstance(moves_str, str):
            return []
        return moves_str.strip().split()

    def make_move(self, move):
        """Wykonuje ruch w formacie UCI."""
        try:
            self.client.board.make_move(self.game_id, move)
            print(f"Wykonano ruch: {move}")
            return True
        except Exception as e:
            print(f"Błąd podczas wykonywania ruchu: {e}")
            return False

    def resign_game(self):
        """Poddaje grę."""
        try:
            self.client.board.resign_game(self.game_id)
            print("Poddałeś partię.")
            self.running = False
            return True
        except Exception as e:
            print(f"Błąd podczas poddawania partii: {e}")
            return False

    def offer_draw(self):
        """Proponuje remis."""
        try:
            self.client.board.offer_draw(self.game_id)
            print("Zaproponowałeś remis.")
            return True
        except Exception as e:
            print(f"Błąd podczas proponowania remisu: {e}")
            return False

    def stop(self):
        """Zatrzymuje klienta."""
        self.running = False
        if self.game_thread and self.game_thread.is_alive():
            self.game_thread.join(timeout=1.0)
