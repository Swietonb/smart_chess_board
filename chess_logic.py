# chess_logic.py
import time
from config import MAPPING, LED_TO_CHESS, COLOR_RED, COLOR_YELLOW, COLOR_ORANGE

# Przechowuje stan pulsacji (dla efektu migania)
pulse_state = False
last_pulse_change = time.time()


def process_data(reed_data):
    """
    Przetwarza dane z przełączników Reeda i zwraca informacje o tym,
    które diody należy zapalić i w jakim kolorze.

    Logika:
    - Pola startowe (linie 1,2,7,8):
      - Jeśli figura obecna: dioda WYŁĄCZONA
      - Jeśli brak figury: dioda pulsująca żółto-pomarańczowa
    - Pola środkowe (linie 3,4,5,6):
      - Jeśli figura obecna: dioda CZERWONA
      - Jeśli brak figury: dioda WYŁĄCZONA
    """
    global pulse_state, last_pulse_change

    current_time = time.time()
    if current_time - last_pulse_change > 0.2:
        pulse_state = not pulse_state
        last_pulse_change = current_time

    # Kolor dla pulsacji
    pulse_color = COLOR_YELLOW if pulse_state else COLOR_ORANGE

    # Lista diod z informacją o kolorze
    leds_with_colors = []

    for mcp_name, ports in reed_data.items():
        for port_name, pins in ports.items():
            for pin_name, state in pins.items():
                led_num = MAPPING[mcp_name][port_name][pin_name]

                if led_num in LED_TO_CHESS:
                    chess_pos = LED_TO_CHESS[led_num]
                    rank = chess_pos[1]  # Numer linii (1-8)

                    # Linie początkowe (1,2,7,8)
                    if rank in ['1', '2', '7', '8']:
                        if state == 0:  # Brak figury, pulsowanie
                            leds_with_colors.append({"led": led_num, "color": pulse_color})
                        # Jeśli figura jest obecna, nie dodajemy LED (pozostaje wyłączony)

                    # Linie środkowe (3,4,5,6)
                    elif rank in ['3', '4', '5', '6'] and state == 1:  # Figura na środku
                        leds_with_colors.append({"led": led_num, "color": COLOR_RED})

    return leds_with_colors


def is_board_ready(reed_data):
    """
    Sprawdza czy szachownica jest gotowa do gry bezpośrednio na podstawie stanu przełączników Reed.

    Szachownica jest gotowa gdy:
    - Wszystkie przełączniki Reed na liniach startowych (1,2,7,8) mają wartość 1 (figura obecna)
    - Wszystkie przełączniki Reed na polach środkowych (3,4,5,6) mają wartość 0 (brak figury)
    """
    for mcp_name, ports in reed_data.items():
        for port_name, pins in ports.items():
            for pin_name, state in pins.items():
                led_num = MAPPING[mcp_name][port_name][pin_name]

                if led_num in LED_TO_CHESS:
                    chess_pos = LED_TO_CHESS[led_num]
                    rank = chess_pos[1]  # Numer linii (1-8)

                    # Sprawdź linie startowe (1,2,7,8)
                    if rank in ['1', '2', '7', '8']:
                        if state != 1:  # Powinna być figura (Reed=1)
                            return False

                    # Sprawdź pola środkowe (3,4,5,6)
                    elif rank in ['3', '4', '5', '6']:
                        if state != 0:  # Nie powinno być figury (Reed=0)
                            return False

    # Jeśli nie znaleźliśmy żadnego nieprawidłowego stanu, szachownica jest gotowa
    return True
