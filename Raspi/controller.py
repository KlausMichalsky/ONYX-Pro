# =======================================================================
#                     🔹 O N Y X - P R O 🔹
# =======================================================================
# Archivo : controller.py
# Descripción:
#     - Coordinación de los turnos de la partida.
#     - Gestión del turno humano.
# =======================================================================

import sensors

from robot import (
    clear_input_buffer,
    execute_robot_move,
)

from stockfish import get_best_move

from game import (
    process_human_move,
    push_move,
    mirror_move,
    prepare_robot_move,
    sensor_occupancy_from_board,
    is_game_over,
)

from maintenance import MaintenanceConsole

# =========================
# TURNO HUMANO
# =========================


def run_human_turn(
    board,
    confirmed_state,
    change_history,
    mirror_coordinates,
    maintenance_callback=None,
):
    """Gestiona el turno humano y devuelve el estado confirmado."""

    print("\n♟️ Mové tus piezas y pulsá el botón para confirmar.")
    print("Podés corregir tus movimientos antes de confirmar.")

    while True:

        # Esperar el botón y obtener el estado del tablero.
        current_state = sensors.wait_for_human_confirmation(
            confirmed_state,
            change_history,
            maintenance_callback=maintenance_callback,
        )

        # Si el tablero volvió a la posición confirmada.
        if current_state is None:
            print("↩️ Tablero restaurado. Podés volver a mover.")
            continue

        try:
            # Identificar y validar la jugada humana.
            logical_move, human_move = process_human_move(
                board,
                confirmed_state,
                current_state,
                change_history,
                mirror_coordinates,
            )

        except (ValueError, IndexError) as error:
            print(f"❌ Jugada no confirmada: {error}")
            print("Corregí las piezas y volvé a pulsar.")
            continue

        # Mostrar las coordenadas físicas y lógicas.
        physical_move = (
            mirror_move(logical_move)
            if mirror_coordinates
            else logical_move
        )

        push_move(board, human_move)

        print("👤 Human_Physical_Board:", physical_move)
        print("👤 Human_Stockfish_Board:", logical_move)

        # Actualizar la posición confirmada.
        confirmed_state = current_state.copy()
        change_history.clear()

        return confirmed_state


# =========================
# TURNO ROBOT
# =========================

def run_robot_turn(board, mirror_coordinates, change_history):
    """Ejecuta la jugada del robot y sincroniza los sensores."""

    # Limpiar mensajes pendientes del puerto serie.
    clear_input_buffer()

    # Obtener la mejor jugada de Stockfish.
    stockfish_move = get_best_move(board)

    # Preparar las coordenadas físicas y los datos de captura.
    move, robot_move, capture_square, from_square = prepare_robot_move(
        board,
        stockfish_move,
        mirror_coordinates,
    )

    print("🤖 Robot_Stockfish_Board:", stockfish_move)
    print("🤖 Robot_Physical_Board:", robot_move)

    # Ejecutar el movimiento o la captura.
    if capture_square is not None and from_square is not None:
        execute_robot_move(
            robot_move,
            capture_square,
            from_square,
        )
    else:
        execute_robot_move(robot_move)

    # Actualizar el tablero lógico.
    push_move(board, move)

    # Sincronizar los sensores con la posición esperada.
    confirmed_state = sensors.read_stable_sensor_state()

    expected_state = sensor_occupancy_from_board(
        board,
        mirror_coordinates,
    )

    confirmed_state = sensors.synchronize_board(
        expected_state,
        confirmed_state,
        change_history,
    )

    return confirmed_state


# =========================
# BUCLE PRINCIPAL DE PARTIDA
# =========================
def run_game_loop(
    board,
    human_turn,
    mirror_coordinates,
    confirmed_state,
    change_history,
    maintenance_mode=False,
):
    """Coordina los turnos hasta que termina la partida."""
    maintenance_console = (
        MaintenanceConsole() if maintenance_mode else None
    )
    while True:

        if human_turn:
            confirmed_state = run_human_turn(
                board,
                confirmed_state,
                change_history,
                mirror_coordinates,
                maintenance_callback=(
                    maintenance_console.poll if maintenance_console else None
                ),
            )

            human_turn = False

        else:
            confirmed_state = run_robot_turn(
                board,
                mirror_coordinates,
                change_history,
            )

            human_turn = True

        # Comprobar el final después de cada turno.
        if is_game_over(board):
            return
