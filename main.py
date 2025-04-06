from chess_server import ChessServer
from lichess_client import LichessClient
from chess_move_handler import ChessMoveHandler
from config import LICHESS_API_TOKEN, COLOR_GREEN
import threading
import time

# Obiekty globalne
lichess_client = None
chess_server = None
move_handler = None


def handle_opponent_move(move):
    """Funkcja wywoływana, gdy przeciwnik wykona ruch."""
    global move_handler
    print(f"Przeciwnik wykonał ruch: {move}")

    # Ustaw flagę, że teraz jest twoja tura
    if move_handler:
        move_handler.set_player_turn(True)


def handle_my_turn():
    """Funkcja wywoływana, gdy jest Twoja kolej."""
    global move_handler
    print("\nTwój ruch! Podnieś figurę, którą chcesz ruszyć, i postaw ją na polu docelowym.")

    # Ustaw flagę, że teraz jest twoja tura
    if move_handler:
        move_handler.set_player_turn(True)


def handle_reed_changes(changes):
    """Funkcja wywoływana, gdy zmienia się stan przełączników Reed."""
    global move_handler
    if move_handler:
        move_handler.handle_reed_change(changes)


def on_board_ready():
    """Funkcja wywoływana, gdy szachownica jest gotowa."""
    global lichess_client, chess_server, move_handler

    print("\n=== SZACHOWNICA GOTOWA ===")
    print("Wszystkie figury są ustawione w pozycji startowej.\n")

    # Pobierz ID partii od użytkownika
    game_id = input("Podaj ID partii Lichess: ")

    # Włącz tryb gry w serwerze szachownicy
    chess_server.set_game_mode(True)

    # Inicjalizacja klienta Lichess
    lichess_client = LichessClient(
        api_token=LICHESS_API_TOKEN,
        on_opponent_move=handle_opponent_move,
        on_my_turn=handle_my_turn
    )

    # Inicjalizacja obsługi ruchów
    move_handler = ChessMoveHandler(chess_server, lichess_client)

    # Rozpoczęcie gry
    lichess_client.start_game(game_id)


def main():
    print("=== SERWER SZACHOWNICY ===")

    # Inicjalizacja i uruchomienie serwera
    global chess_server
    chess_server = ChessServer(
        on_board_ready=on_board_ready,
        on_reed_change=handle_reed_changes
    )

    # Dodaj referencje do mapowań
    from config import MAPPING, LED_TO_CHESS, CHESS_TO_LED, BUFFER_SIZE
    chess_server.MAPPING = MAPPING
    chess_server.LED_TO_CHESS = LED_TO_CHESS
    chess_server.CHESS_TO_LED = CHESS_TO_LED
    chess_server.BUFFER_SIZE = BUFFER_SIZE

    # Uruchom serwer
    chess_server.start()

    print("Serwer uruchomiony. Aby zakończyć, naciśnij Ctrl+C")

    try:
        # Utrzymuj główny wątek działający
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nZatrzymywanie serwera...")

        # Zatrzymaj komponenty
        if lichess_client:
            lichess_client.stop()
        if move_handler:
            move_handler.stop()
        chess_server.stop()


if __name__ == "__main__":
    main()
