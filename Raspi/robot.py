# =======================================================================
#                         🔹 O N Y X - P R O 🔹
# =======================================================================
#  Archivo   : robot.py
#  Autor     : Klaus Michalsky
#  Fecha     : Oct-2026
# -----------------------------------------------------------------------
#  ▫️ DESCRIPCIÓN
#     - Comunicación con el RP2040
#     - Detección del puerto serie
#     - Envío y recepción de comandos
#     - Reset y homing del robot
# =======================================================================

import glob  # glob es un módulo de Python que permite buscar archivos

# o rutas que coincidan con un patrón. Es decir, para encontrar automáticamente el puerto donde Linux detectó el RP2040.
import time
import serial

from config import BAUDRATE, SERIAL_TIMEOUT

# =========================
# SERIAL INIT
# =========================

SERIAL_PORT = None
ser = None


def check_shutdown_request():
    """Comprueba si se solicitó apagar la Raspberry Pi."""

    import sensors

    sensors.check_shutdown_request()


def initialize_serial():
    """Detecta el puerto USB e inicia la conexión serie con el RP2040."""

    global SERIAL_PORT, ser

    if ser is not None and ser.is_open:
        return

    ports = glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")

    if not ports:
        raise RuntimeError("No se encontró RP2040 conectado")

    SERIAL_PORT = ports[0]

    print("Usando puerto:", SERIAL_PORT)
    print("🤖 Iniciando ONYX-Pro...")

    ser = serial.Serial(
        SERIAL_PORT,
        BAUDRATE,
        timeout=SERIAL_TIMEOUT,
    )

    time.sleep(2)


# =========================
# RESET ROBOT
# =========================


def reset_robot():
    ser.write(b"RESET\n")
    time.sleep(0.5)
    ser.reset_input_buffer()


# =========================
# SEND COMMAND
# =========================
def send_to_robot(cmd):
    print(f"📤 Enviando al RP2040: [{cmd}]")
    ser.write((cmd + "\n").encode())
    # encode() convierte el texto en bytes


# "e2e4\n"
#       ↓ encode()
# b"e2e4\n"
# ser.write() envía solo bytes al RP2040 a través del puerto serial.


# =========================
# LIMPIAR BUFFER SERIE
# =========================


def clear_input_buffer():
    """Descarta mensajes pendientes en la entrada serie del RP2040."""
    ser.reset_input_buffer()


# =========================
# INICIALIZAR ROBOT
# =========================
def initialize_robot():
    """Reinicia el RP2040 y prepara el contador de capturas."""

    print("Reset RP2040...")
    reset_robot()

    # Esperar a que el RP2040 esté listo.
    time.sleep(1)

    # Reiniciar el contador del Capture-Board.
    send_to_robot("CAPTURERESET")


# =========================
# LEER RESPUESTA SERIE
# =========================


def read_robot_line():
    """Lee y muestra una línea recibida del RP2040."""

    line = ser.readline().decode(errors="ignore").strip()

    if line:
        print("RP2040:", line)

    return line


# =========================
# CONFIGURACIÓN DE OFFSETS
# =========================


def get_offsets():
    """Consulta los offsets actuales del RP2040."""

    send_to_robot("GET_OFFSETS")
    ser.flush()

    deadline = time.monotonic() + 3

    while time.monotonic() < deadline:

        line = read_robot_line()

        if line.startswith("OFFSETS X="):
            try:
                values = line.replace("OFFSETS ", "").split()

                offset_x = float(values[0].split("=")[1])
                offset_y = float(values[1].split("=")[1])

                return offset_x, offset_y

            except (ValueError, IndexError):
                raise RuntimeError("Respuesta de offsets inválida")

    raise TimeoutError("El RP2040 no respondió a GET_OFFSETS")


def set_offsets(offset_x, offset_y):
    """Envía nuevos offsets al RP2040."""

    command = f"SET_OFFSETS {offset_x:.2f} {offset_y:.2f}"

    send_to_robot(command)
    ser.flush()

    deadline = time.monotonic() + 3

    while time.monotonic() < deadline:

        line = read_robot_line()

        if line.startswith("OFFSETS OK"):
            return True

        if line.startswith("ERROR"):
            raise RuntimeError(line)

    raise TimeoutError("El RP2040 no confirmó SET_OFFSETS")


# =========================
# WAIT DONE
# =========================


def wait_done():

    while True:

        check_shutdown_request()

        line = read_robot_line()

        if line and "DONE" in line:
            break


# =========================
# HOMING
# =========================


def do_homing():

    print("🤖 Enviando HOMING...")
    ser.write(b"HOMING\n")

    while True:

        check_shutdown_request()

        line = read_robot_line()

        if line and "DONE" in line:
            print("✅ HOMING COMPLETO")
            break


# =========================
# WAIT ANY
# =========================


def wait_any(*expected):

    while True:

        check_shutdown_request()

        line = read_robot_line()

        if line and any(e in line for e in expected):
            return


# =========================
# SHUTDOWN
# =========================


def shutdown_robot():
    try:
        if ser.is_open:
            ser.write(b"MOTOROFF\n")
            ser.flush()
            time.sleep(0.2)
    except Exception as e:
        print(f"⚠️ Error al apagar los motores: {e}")
    finally:
        try:
            if ser.is_open:
                ser.close()
        except Exception:
            pass


def execute_robot_move(robot_move, capture_square=None, from_square=None):
    if capture_square is not None and from_square is not None:
        destination_square = robot_move[2:4]

        send_to_robot(f"REMOVE {capture_square} {from_square} {destination_square}")
        wait_any("MOVE DONE", "CAPTURE DONE")
        print("✅ Captura completada")

    else:
        send_to_robot(robot_move)
        wait_done()
