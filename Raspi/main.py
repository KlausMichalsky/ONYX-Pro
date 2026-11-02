# =======================================================================
#                         🔹 O N Y X - P R O 🔹
# =======================================================================
#  Archivo   : main.py
#  Autor     : Klaus Michalsky
#  Fecha     : Oct-2026
# -----------------------------------------------------------------------
#  ▫️ DESCRIPCIÓN
#     - Control principal de ONYX-Pro
#     - Gestión de partida de ajedrez
#     - Comunicación con RP2040
#     - Control de Stockfish
# =======================================================================


import signal

import subprocess

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

initialize_serial()

initialize_stockfish()

initialize_robot()

sensors.init_button()

board = create_board()


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
    # Al pulsar Ctrl+C, se ejecutará el apagado del robot y se cerrará la conexión serie
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


# =========================
# START
# =========================

print("🤖 ONYX-Pro READY")


try:

    do_homing()

    # ---------------------------------------------------------
    # SELECCIÓN DEL MODO DE JUEGO
    # ---------------------------------------------------------

    # Para seleccionar modo Humano/Robot mediante teclado,
    # activar este bloque y desactivar el siguiente:
    # mode = input("\n¿Quién empieza? (1=Humano, 2=Robot): ").strip()
    # human_turn = (mode == "1")
    # mirror_coordinates = (mode == "1")

    # Para seleccionar modo Humano/Robot mediante USER-Button,
    # activar este bloque y desactivar el anterior:
    mode = sensors.select_start_mode()
    human_turn = (mode == "1")
    mirror_coordinates = (mode == "1")

    # Arranque automático al iniciar Raspberry Pi:
    # sudo systemctl enable --now onyx.service
    #
    # Arranque manual desde terminal:
    # sudo systemctl disable --now onyx.service

    # =========================
    # SENSORES Y BOTÓN
    # =========================
    expected_state = sensor_occupancy_from_board(
        board,
        mirror_coordinates,
    )

    confirmed_state = sensors.initialize_and_validate_sensors(
        expected_state,
    )

    change_history = []

    print("\n♟️ Iniciando partida...\n")

    # =========================
    # LOOP PRINCIPAL
    # =========================

    run_game_loop(
        board,
        human_turn,
        mirror_coordinates,
        confirmed_state,
        change_history,
    )

    # =========================
    # FIN PARTIDA
    # =========================

    if is_game_over(board):
        print("\n🏁 Fin de partida")
        print(get_result(board))

        shutdown()


except sensors.ShutdownRequested:

    print("\n🛑 Apagado solicitado mediante el botón GPIO18.")

    shutdown()
    poweroff_system()
