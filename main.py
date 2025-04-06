# main.py
from chess_server import ChessServer
from lichess_client import LichessClient
from config import LICHESS_API_TOKEN
import threading
import time

# Flagi do koordynacji
lichess_client = None
waiting_for_user_move = False
user_move_thread = None


def handle_opponent_move(move):
    """Funkcja wywoływana, gdy przeciwnik wykona ruch."""
    # W przyszłości tu będzie kod do obsługi ruchu przeciwnika na szachownicy
    print(f"Przeciwnik wykonał ruch: {move}")


def handle_my_turn():
    """Funkcja wywoływana, gdy jest Twoja kolej."""
    global waiting_for_user_move, user_move_thread

    # Jeśli już czekamy na ruch użytkownika, nie rób nic
    if waiting_for_user_move:
        return

    # Rozpocznij nowy wątek do pobierania ruchu od użytkownika
    waiting_for_user_move = True
    user_move_thread = threading.Thread(target=get_and_make_move)
    user_move_thread.daemon = True
    user_move_thread.start()


def get_and_make_move():
    """Pobiera ruch od użytkownika i wykonuje go."""
    global waiting_for_user_move, lichess_client

    print("\nTwój ruch!")
    while waiting_for_user_move:
        user_move = get_user_move()

        if user_move == 'resign':
            lichess_client.resign_game()
            waiting_for_user_move = False
            break
        elif user_move == 'draw':
            lichess_client.offer_draw()
            # Nie kończymy czekania, bo przeciwnik może odrzucić remis
        else:
            success = lichess_client.make_move(user_move)
            if success:
                waiting_for_user_move = False
                break
            # Jeśli ruch się nie powiódł, prosimy o podanie ruchu ponownie


def get_user_move():
    """Pobiera ruch od użytkownika w formacie UCI."""
    while True:
        user_move = input("Twój ruch (w formacie UCI, np. e2e4): ").strip().lower()

        # Obsługa specjalnych komend
        if user_move in ['resign', 'draw']:
            return user_move

        # Podstawowe sprawdzanie formatu UCI
        if len(user_move) >= 4 and all(c in "abcdefgh12345678" for c in user_move[:4]):
            return user_move

        print("Niepoprawny format ruchu. Spróbuj ponownie.")
        print("Możesz też napisać 'resign' aby poddać partię lub 'draw' aby zaproponować remis.")


def on_board_ready():
    """Funkcja wywoływana, gdy szachownica jest gotowa."""
    global lichess_client

    print("\n=== SZACHOWNICA GOTOWA ===")
    print("Wszystkie figury są ustawione w pozycji startowej.\n")

    # Pobierz ID partii od użytkownika
    game_id = input("Podaj ID partii Lichess: ")

    # Inicjalizacja klienta Lichess
    lichess_client = LichessClient(
        api_token=LICHESS_API_TOKEN,
        on_opponent_move=handle_opponent_move,
        on_my_turn=handle_my_turn
    )

    # Rozpoczęcie gry
    lichess_client.start_game(game_id)


def main():
    print("=== SERWER SZACHOWNICY ===")

    # Inicjalizacja i uruchomienie serwera
    server = ChessServer(on_board_ready=on_board_ready)
    server.start()

    print("Serwer uruchomiony. Aby zakończyć, naciśnij Ctrl+C")

    try:
        # Utrzymuj główny wątek działający
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nZatrzymywanie serwera...")

        # Zatrzymaj klienta Lichess jeśli istnieje
        global lichess_client
        if lichess_client:
            lichess_client.stop()

        server.stop()


if __name__ == "__main__":
    main()
