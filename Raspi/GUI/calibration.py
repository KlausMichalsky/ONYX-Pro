import tkinter as tk
from tkinter import messagebox
import math

import robot


# =========================================================
# ONYX-Pro GUI - MACHINE CALIBRATION
# XY OFFSET ADJUSTMENT
# =========================================================

BG = "#10151D"
PANEL = "#1C2633"
PANEL_LIGHT = "#253344"

BLUE = "#168BE1"
BLUE_HOVER = "#269FF5"

TEXT = "#E8EDF5"
MUTED = "#8292A7"

GREEN = "#38C98A"
RED = "#F06464"
YELLOW = "#F5C451"
BORDER = "#344154"
DISABLED = "#465365"

STEP_UNITS = 1  # 0.5 mm, stored as half-millimeter units

X_MIN = -145.0
X_MAX = -135.0

Y_MIN = 116.0
Y_MAX = 126.0

DEFAULT_X = -140.0
DEFAULT_Y = 121.0


class CalibrationScreen:

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app

        self.offset_x = tk.IntVar(value=round(DEFAULT_X * 2))
        self.offset_y = tk.IntVar(value=round(DEFAULT_Y * 2))

        self.connection_status = tk.StringVar(value="DISCONNECTED")
        self.build_screen()

    # -----------------------------------------------------
    # SCREEN
    # -----------------------------------------------------

    def build_screen(self):
        header = tk.Frame(self.parent, bg=BG)
        header.pack(fill="x", padx=24, pady=(15, 5))

        back_button = tk.Button(
            header,
            text="←",
            font=("Arial", 20, "bold"),
            bg=PANEL,
            fg=TEXT,
            activebackground=BLUE,
            activeforeground="white",
            relief="flat",
            bd=0,
            width=3,
            command=self.close_screen,
        )
        back_button.pack(side="left", padx=(0, 14))

        tk.Label(
            header,
            text="MACHINE CALIBRATION",
            font=("Arial", 15, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack(side="left", pady=7)

        self.status_label = tk.Label(
            header,
            textvariable=self.connection_status,
            font=("Arial", 9, "bold"),
            bg=BG,
            fg=MUTED,
        )
        self.status_label.pack(side="right", pady=10)

        tk.Frame(self.parent, bg=BORDER, height=1).pack(
            fill="x", padx=24, pady=7
        )

        main = tk.Frame(self.parent, bg=BG)
        main.pack(fill="both", expand=True, padx=28, pady=(5, 8))

        tk.Label(
            main,
            text="XY COORDINATE OFFSETS",
            font=("Arial", 18, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack(anchor="w")

        tk.Label(
            main,
            text="Adjust the machine reference position in millimeters",
            font=("Arial", 9),
            bg=BG,
            fg=MUTED,
        ).pack(anchor="w", pady=(2, 10))

        offset_frame = tk.Frame(main, bg=BG)
        offset_frame.pack(fill="x")

        offset_frame.columnconfigure(0, weight=1)
        offset_frame.columnconfigure(1, weight=1)

        self.x_value_label, self.x_up, self.x_down = self.create_offset_panel(
            offset_frame, 0, "OFFSET X", self.offset_x, X_MIN, X_MAX
        )
        self.y_value_label, self.y_up, self.y_down = self.create_offset_panel(
            offset_frame, 1, "OFFSET Y", self.offset_y, Y_MIN, Y_MAX
        )

        buttons = tk.Frame(main, bg=BG)
        buttons.pack(fill="x", pady=(13, 0))

        self.create_button(buttons, "READ", self.read_offsets, PANEL_LIGHT)
        self.create_button(buttons, "SAVE", self.save_offsets, BLUE)

        tk.Label(
            main,
            text="STEP: 0.5 mm     •     SAVE writes the offsets to the RP2040",
            font=("Arial", 8, "bold"),
            bg=BG,
            fg=MUTED,
        ).pack(anchor="center", pady=(8, 0))

    # -----------------------------------------------------
    # OFFSET PANELS
    # -----------------------------------------------------

    @staticmethod
    def format_value(value):
        return f"{value / 2:.1f}"

    @staticmethod
    def valid_value(value, minimum, maximum):
        if not math.isfinite(value):
            return False
        if value < minimum or value > maximum:
            return False
        return abs(value * 2 - round(value * 2)) < 0.000001

    def create_offset_panel(self, parent, column, label, value_var, minimum, maximum):
        panel = tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        panel.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(0, 7) if column == 0 else (7, 0),
        )

        tk.Label(
            panel,
            text=label,
            font=("Arial", 10, "bold"),
            bg=PANEL,
            fg=MUTED,
        ).pack(anchor="w", padx=15, pady=(10, 6))

        controls = tk.Frame(panel, bg=PANEL)
        controls.pack(fill="x", padx=15, pady=(0, 4))

        value_label = tk.Label(
            controls,
            text="",
            font=("Arial", 23, "bold"),
            bg=PANEL_LIGHT,
            fg="#60A5FA",
            width=10,
            pady=8,
        )
        value_label.pack(side="left", fill="x", expand=True)

        arrows = tk.Frame(controls, bg=PANEL)
        arrows.pack(side="right", padx=(10, 0))

        up_button = tk.Button(
            arrows,
            text="▲",
            font=("Arial", 15, "bold"),
            bg=BLUE,
            fg="white",
            activebackground=BLUE_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            width=3,
            command=lambda: self.change_value(
                value_var, 1, value_label, up_button, down_button, minimum, maximum
            ),
        )
        up_button.pack(pady=(0, 4), ipady=2)

        down_button = tk.Button(
            arrows,
            text="▼",
            font=("Arial", 15, "bold"),
            bg=BLUE,
            fg="white",
            activebackground=BLUE_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            width=3,
            command=lambda: self.change_value(
                value_var, -1, value_label, up_button, down_button, minimum, maximum
            ),
        )
        down_button.pack(ipady=2)

        tk.Label(
            panel,
            text="STEP: 0.5 mm",
            font=("Arial", 8, "bold"),
            bg=PANEL,
            fg=MUTED,
        ).pack(anchor="w", padx=15, pady=(2, 9))

        self.update_panel(
            value_var, value_label, up_button, down_button, minimum, maximum
        )
        return value_label, up_button, down_button

    def change_value(
        self, value_var, direction, value_label, up_button, down_button, minimum, maximum
    ):
        new_value = value_var.get() + direction * STEP_UNITS
        min_units = round(minimum * 2)
        max_units = round(maximum * 2)

        if min_units <= new_value <= max_units:
            value_var.set(new_value)
            self.update_panel(
                value_var, value_label, up_button, down_button, minimum, maximum
            )

    def update_panel(
        self, value_var, value_label, up_button, down_button, minimum, maximum
    ):
        value = value_var.get() / 2
        value_label.configure(text=f"{value:.1f} mm")

        up_enabled = value < maximum
        down_enabled = value > minimum

        up_button.configure(
            state=tk.NORMAL if up_enabled else tk.DISABLED,
            bg=BLUE if up_enabled else DISABLED,
        )
        down_button.configure(
            state=tk.NORMAL if down_enabled else tk.DISABLED,
            bg=BLUE if down_enabled else DISABLED,
        )

    # -----------------------------------------------------
    # SERIAL COMMUNICATION
    # -----------------------------------------------------

    def update_status(self, text, color, system_status=None, detail=None):
        self.connection_status.set(text)
        self.status_label.configure(fg=color)

        if system_status:
            self.app.set_status(system_status, detail or text)

    def ensure_connection(self):
        if robot.ser is None or not robot.ser.is_open:
            self.update_status(
                "CONNECTING...", BLUE, "BUSY", "CONNECTING TO RP2040"
            )
            robot.initialize_serial()

        if robot.ser is None or not robot.ser.is_open:
            raise RuntimeError("Could not establish serial connection.")

    def read_offsets(self):
        try:
            self.ensure_connection()
            self.update_status("READING...", BLUE, "BUSY", "READING XY OFFSETS")

            x, y = robot.get_offsets()

            if not self.valid_value(x, X_MIN, X_MAX):
                raise ValueError(f"RP2040 returned an invalid X offset: {x}")

            if not self.valid_value(y, Y_MIN, Y_MAX):
                raise ValueError(f"RP2040 returned an invalid Y offset: {y}")

            self.offset_x.set(round(x * 2))
            self.offset_y.set(round(y * 2))

            self.update_panel(
                self.offset_x, self.x_value_label, self.x_up, self.x_down, X_MIN, X_MAX
            )
            self.update_panel(
                self.offset_y, self.y_value_label, self.y_up, self.y_down, Y_MIN, Y_MAX
            )

            self.update_status("CONNECTED", GREEN, "READY", "RP2040 CONNECTED")

        except Exception as error:
            self.update_status(
                "CONNECTION ERROR", RED, "ERROR", "RP2040 COMMUNICATION FAILED"
            )
            messagebox.showerror("ONYX-Pro", f"Could not read offsets:\n\n{error}")

    def save_offsets(self):
        x = self.offset_x.get() / 2
        y = self.offset_y.get() / 2

        try:
            if not self.valid_value(x, X_MIN, X_MAX):
                raise ValueError("OFFSET X is outside the permitted range.")

            if not self.valid_value(y, Y_MIN, Y_MAX):
                raise ValueError("OFFSET Y is outside the permitted range.")

            self.ensure_connection()
            self.update_status("SENDING...", BLUE, "BUSY", "SAVING XY OFFSETS")

            success = robot.set_offsets(x, y)
            if not success:
                raise RuntimeError("RP2040 did not confirm the offsets.")

            actual_x, actual_y = robot.get_offsets()

            if not self.valid_value(actual_x, X_MIN, X_MAX):
                raise RuntimeError("Invalid X value returned by RP2040.")

            if not self.valid_value(actual_y, Y_MIN, Y_MAX):
                raise RuntimeError("Invalid Y value returned by RP2040.")

            if abs(actual_x - x) > 0.001 or abs(actual_y - y) > 0.001:
                raise RuntimeError(
                    "The returned offsets do not match the saved values."
                )

            self.update_status("CONNECTED", GREEN, "READY", "XY OFFSETS SAVED")
            messagebox.showinfo("ONYX-Pro", "Offsets updated successfully!")

        except ValueError as error:
            self.update_status("INVALID VALUES", RED, "WARNING", "CHECK XY LIMITS")
            messagebox.showwarning("Invalid values", str(error))

        except Exception as error:
            self.update_status(
                "CONNECTION ERROR", RED, "ERROR", "RP2040 COMMUNICATION FAILED"
            )
            messagebox.showerror("ONYX-Pro", f"Could not save offsets:\n\n{error}")

    # -----------------------------------------------------
    # BUTTONS / NAVIGATION
    # -----------------------------------------------------

    @staticmethod
    def create_button(parent, text, command, color):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Arial", 11, "bold"),
            bg=color,
            fg="white",
            activebackground=BLUE_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        button.pack(side="left", expand=True, fill="x", padx=5, ipady=9)
        return button

    def close_screen(self):
        # Release the USB serial port when leaving calibration.
        # The robot engine can open it again when a game is started.
        try:
            if robot.ser is not None and robot.ser.is_open:
                robot.ser.close()
        except Exception:
            pass

        self.app.set_status("IDLE", "ROBOT NOT INITIALIZED")
        self.app.show_home()
