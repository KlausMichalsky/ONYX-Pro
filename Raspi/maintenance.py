
import sys
import select

from robot import send_to_robot


class MaintenanceConsole:
    """Consola opcional de mantenimiento durante el turno humano."""

    def __init__(self):
        self.active = True

    def poll(self):
        if not self.active or not sys.stdin.isatty():
            return

        ready, _, _ = select.select([sys.stdin], [], [], 0)

        if not ready:
            return

        command = sys.stdin.readline().strip().upper()

        if command == "HELP":
            print("\nComandos disponibles:")
            print("  XYOFF  - Deshabilitar motores XY")
            print("  XYON   - Habilitar motores XY")
            print("  EXIT   - Desactivar consola")
            return

        if command in ("XYOFF", "XYON"):
            send_to_robot(command)
            return

        if command == "EXIT":
            self.active = False
            print("🔧 Consola de mantenimiento desactivada.")
            return

        if command:
            print("❌ Comando desconocido. Escribí HELP.")
