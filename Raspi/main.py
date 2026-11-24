
# =======================================================================
#                         🔹 O N Y X - P R O 🔹
# =======================================================================
# Archivo   : main.py
# Autor     : Klaus Michalsky
# Descripción:
#     - Control principal de ONYX-Pro
#     - Gestión de partidas consecutivas
#     - Comunicación con RP2040
#     - Control de Stockfish
# =======================================================================

import signal
import subprocess
import sys

import sensors

from robot import (
    do_homing,
    shutdown_robot,
    initialize_robot,
    initialize_serial,
)

from stockfish import (
    initialize_stockfish,
    shutdown_stockfish,
)

from game import (
    create_board,
    is_game_over,
    get_result,
    sensor_occupancy_from_board,
)

from controller import run_game_loop


# =========================
# SHUTDOWN
# =========================

def shutdown():
    """Cierra sensores, Stockfish y robot aunque falle una etapa."""

    shutdown_steps = (
        ("sensores", sensors.shutdown_sensors),
        ("Stockfish", shutdown_stockfish),
        ("robot", shutdown_robot),
    )

    for name, close_function in shutdown_steps:
        try:
            close_function()
        except Exception as error:
            print(f"⚠️ Error al cerrar {name}: {error}")


def handle_interrupt(signum, frame):
    """Gestiona la interrupción mediante Ctrl+C."""

    print("\n⚠️ Interrupción: apagando ONYX-Pro...")
    shutdown()
    raise SystemExit(130)


signal.signal(signal.SIGINT, handle_interrupt)


# =========================
# APAGADO SEGURO RASPBERRY PI
# =========================

def poweroff_system():
    """Apaga Raspberry Pi mediante systemd."""

    print("🔌 Apagando Raspberry Pi...")

    try:
        subprocess.run(
            ["sudo", "-n", "/usr/bin/systemctl", "poweroff"],
            check=True,
        )

    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        print(f"⚠️ No se pudo apagar Raspberry Pi: {error}")
        raise SystemExit(1)

    raise SystemExit(0)


MAINTENANCE_MODE = "--maintenance" in sys.argv

if MAINTENANCE_MODE:
    print("🔧 ONYX-Pro: MODO MANTENIMIENTO")

# =========================
# INICIALIZACIÓN GENERAL
# =========================
initialize_serial()
initialize_stockfish()
sensors.init_button()

print("🤖 ONYX-Pro READY")


# =========================
# CICLO PRINCIPAL
# =========================

try:

    while True:

        # Crear un tablero nuevo para cada partida.
        board = create_board()

        # Preparar el robot y reiniciar el contador de capturas.
        initialize_robot()

        # Ejecutar homing antes de cada partida.
        do_homing()

        # -----------------------------------------
        # SELECCIÓN DEL MODO DE JUEGO
        # -----------------------------------------

        mode = sensors.select_start_mode()

        human_turn = (mode == "1")
        mirror_coordinates = (mode == "1")

        # -----------------------------------------
        # SENSORES Y BOTÓN
        # -----------------------------------------

        expected_state = sensor_occupancy_from_board(
            board,
            mirror_coordinates,
        )

        confirmed_state = sensors.initialize_and_validate_sensors(
            expected_state,
        )

        change_history = []

        print("\n♟️ Iniciando partida...\n")

        # -----------------------------------------
        # LOOP DE LA PARTIDA
        # -----------------------------------------

        run_game_loop(
            board,
            human_turn,
            mirror_coordinates,
            confirmed_state,
            change_history,
            maintenance_mode=MAINTENANCE_MODE,
        )

        # -----------------------------------------
        # FIN DE PARTIDA
        # -----------------------------------------

        if is_game_over(board):

            print("\n🏁 Fin de partida")
            print(get_result(board))

            # Esperar una pulsación corta para una nueva partida.
            sensors.wait_for_new_game()

            print("\n🔄 Reiniciando ciclo de juego...\n")

            continue


except sensors.ShutdownRequested:

    print("\n🛑 Apagado solicitado mediante el botón GPIO17.")

    shutdown()
    poweroff_system()
