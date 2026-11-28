import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import sys
import math

# ---------------------------------------------------------
# ONYX-Pro GUI - MACHINE CALIBRATION
# ---------------------------------------------------------

RASPI_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RASPI_DIR))

import robot

# ---------------------------------------------------------
# CONFIGURATION / SAFETY LIMITS
# ---------------------------------------------------------

STEP = 0.5

X_MIN = -145.0
X_MAX = -135.0

Y_MIN = 116.0
Y_MAX = 126.0

DEFAULT_X = -140.0
DEFAULT_Y = 121.0

# ---------------------------------------------------------
# COLORS
# ---------------------------------------------------------

BG = "#10151D"
PANEL = "#1C2633"
PANEL_LIGHT = "#253344"
BLUE = "#168BE1"
BLUE_HOVER = "#269FF5"
TEXT = "#E8EDF5"
MUTED = "#8292A7"
GREEN = "#38C98A"
RED = "#F06464"
BORDER = "#344154"
DISABLED = "#465365"

# ---------------------------------------------------------
# WINDOW
# ---------------------------------------------------------

root = tk.Tk()
root.title("ONYX-Pro | Machine Calibration")
root.geometry("800x480")
root.resizable(False, False)
root.configure(bg=BG)

# Store values as integer half-millimeter units.
# This avoids floating-point accumulation errors.

offset_x = tk.IntVar(value=round(DEFAULT_X * 2))
offset_y = tk.IntVar(value=round(DEFAULT_Y * 2))

connection_status = tk.StringVar(value="DISCONNECTED")


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------


def format_value(value):
    return f"{value / 2:.1f}"


def update_status(text, color):
    connection_status.set(text)
    status_label.configure(fg=color)
    root.update_idletasks()


def ensure_connection():
    if robot.ser is None or not robot.ser.is_open:
        update_status("CONNECTING...", BLUE)
        robot.initialize_serial()

    if robot.ser is None or not robot.ser.is_open:
        raise RuntimeError("Could not establish serial connection.")


def valid_value(value, minimum, maximum):
    if not math.isfinite(value):
        return False

    if value < minimum or value > maximum:
        return False

    # Only multiples of 0.5 mm are accepted.
    return abs(value * 2 - round(value * 2)) < 0.000001


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

header = tk.Frame(root, bg=BG)
header.pack(fill="x", padx=28, pady=(20, 10))

logo = tk.Label(header, text="ONYX-Pro", font=("Arial", 25, "bold"), bg=BG, fg=TEXT)
logo.pack(side="left")

subtitle = tk.Label(
    header, text="ROBOT CONTROL SYSTEM", font=("Arial", 9, "bold"), bg=BG, fg=MUTED
)
subtitle.pack(side="left", padx=18, pady=(10, 0))

status_label = tk.Label(
    header, textvariable=connection_status, font=("Arial", 10, "bold"), bg=BG, fg=MUTED
)
status_label.pack(side="right", pady=10)


# ---------------------------------------------------------
# SEPARATOR
# ---------------------------------------------------------

tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=28, pady=8)


# ---------------------------------------------------------
# MAIN CONTENT
# ---------------------------------------------------------

main = tk.Frame(root, bg=BG)
main.pack(fill="both", expand=True, padx=28, pady=8)

tk.Label(
    main, text="MACHINE CALIBRATION", font=("Arial", 19, "bold"), bg=BG, fg=TEXT
).pack(anchor="w")

tk.Label(main, text="XY coordinate offsets", font=("Arial", 10), bg=BG, fg=MUTED).pack(
    anchor="w", pady=(2, 12)
)


# ---------------------------------------------------------
# OFFSET PANELS
# ---------------------------------------------------------

offset_frame = tk.Frame(main, bg=BG)
offset_frame.pack(fill="x")

offset_frame.columnconfigure(0, weight=1)
offset_frame.columnconfigure(1, weight=1)


def update_panel(value_var, value_label, up_button, down_button, minimum, maximum):

    value = value_var.get() / 2

    value_label.configure(text=f"{value:.1f} mm")

    up_button.configure(
        state=tk.NORMAL if value < maximum else tk.DISABLED,
        bg=BLUE if value < maximum else DISABLED,
    )

    down_button.configure(
        state=tk.NORMAL if value > minimum else tk.DISABLED,
        bg=BLUE if value > minimum else DISABLED,
    )


def create_offset_panel(parent, column, label, value_var, minimum, maximum):

    panel = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)

    panel.grid(
        row=0, column=column, sticky="nsew", padx=(0, 8) if column == 0 else (8, 0)
    )

    tk.Label(panel, text=label, font=("Arial", 10, "bold"), bg=PANEL, fg=MUTED).pack(
        anchor="w", padx=18, pady=(13, 8)
    )

    controls = tk.Frame(panel, bg=PANEL)
    controls.pack(fill="x", padx=18, pady=(0, 5))

    value_label = tk.Label(
        controls,
        text="",
        font=("Arial", 25, "bold"),
        bg=PANEL_LIGHT,
        fg="#60A5FA",
        width=11,
        pady=12,
    )
    value_label.pack(side="left", fill="x", expand=True)

    arrows = tk.Frame(controls, bg=PANEL)
    arrows.pack(side="right", padx=(12, 0))

    def change_value(direction):
        current = value_var.get()
        new_value = current + direction

        min_units = round(minimum * 2)
        max_units = round(maximum * 2)

        if min_units <= new_value <= max_units:
            value_var.set(new_value)
            update_panel(
                value_var, value_label, up_button, down_button, minimum, maximum
            )

    up_button = tk.Button(
        arrows,
        text="▲",
        font=("Arial", 17, "bold"),
        bg=BLUE,
        fg="white",
        activebackground=BLUE_HOVER,
        activeforeground="white",
        relief="flat",
        bd=0,
        width=3,
        height=1,
        command=lambda: change_value(1),
    )
    up_button.pack(pady=(0, 5), ipady=3)

    down_button = tk.Button(
        arrows,
        text="▼",
        font=("Arial", 17, "bold"),
        bg=BLUE,
        fg="white",
        activebackground=BLUE_HOVER,
        activeforeground="white",
        relief="flat",
        bd=0,
        width=3,
        height=1,
        command=lambda: change_value(-1),
    )
    down_button.pack(ipady=3)

    tk.Label(
        panel, text="STEP: 0.5 mm", font=("Arial", 8, "bold"), bg=PANEL, fg=MUTED
    ).pack(anchor="w", padx=18, pady=(3, 12))

    update_panel(value_var, value_label, up_button, down_button, minimum, maximum)

    return value_label, up_button, down_button


offset_x_label, x_up, x_down = create_offset_panel(
    offset_frame, 0, "OFFSET X", offset_x, X_MIN, X_MAX
)

offset_y_label, y_up, y_down = create_offset_panel(
    offset_frame, 1, "OFFSET Y", offset_y, Y_MIN, Y_MAX
)


# ---------------------------------------------------------
# READ OFFSETS
# ---------------------------------------------------------


def read_offsets():
    try:
        ensure_connection()
        update_status("READING...", BLUE)

        x, y = robot.get_offsets()

        if not valid_value(x, X_MIN, X_MAX):
            raise ValueError(f"RP2040 returned an invalid X offset: {x}")

        if not valid_value(y, Y_MIN, Y_MAX):
            raise ValueError(f"RP2040 returned an invalid Y offset: {y}")

        offset_x.set(round(x * 2))
        offset_y.set(round(y * 2))

        update_panel(offset_x, offset_x_label, x_up, x_down, X_MIN, X_MAX)

        update_panel(offset_y, offset_y_label, y_up, y_down, Y_MIN, Y_MAX)

        update_status("CONNECTED", GREEN)

    except Exception as error:
        update_status("CONNECTION ERROR", RED)
        messagebox.showerror("ONYX-Pro", f"Could not read offsets:\n\n{error}")


# ---------------------------------------------------------
# SAVE OFFSETS
# ---------------------------------------------------------


def save_offsets():
    x = offset_x.get() / 2
    y = offset_y.get() / 2

    try:
        if not valid_value(x, X_MIN, X_MAX):
            raise ValueError("OFFSET X is outside the permitted range.")

        if not valid_value(y, Y_MIN, Y_MAX):
            raise ValueError("OFFSET Y is outside the permitted range.")

        ensure_connection()
        update_status("SENDING...", BLUE)

        success = robot.set_offsets(x, y)

        if not success:
            raise RuntimeError("RP2040 did not confirm the offsets.")

        actual_x, actual_y = robot.get_offsets()

        if not valid_value(actual_x, X_MIN, X_MAX):
            raise RuntimeError("Invalid X value returned by RP2040.")

        if not valid_value(actual_y, Y_MIN, Y_MAX):
            raise RuntimeError("Invalid Y value returned by RP2040.")

        if abs(actual_x - x) > 0.001 or abs(actual_y - y) > 0.001:
            raise RuntimeError("The returned offsets do not match the saved values.")

        update_status("CONNECTED", GREEN)

        messagebox.showinfo("ONYX-Pro", "Offsets updated successfully!")

    except ValueError as error:
        update_status("INVALID VALUES", RED)
        messagebox.showwarning("Invalid values", str(error))

    except Exception as error:
        update_status("CONNECTION ERROR", RED)
        messagebox.showerror("ONYX-Pro", f"Could not save offsets:\n\n{error}")


# ---------------------------------------------------------
# BUTTONS
# ---------------------------------------------------------

button_frame = tk.Frame(main, bg=BG)
button_frame.pack(fill="x", pady=17)


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

    button.pack(side="left", expand=True, fill="x", padx=5, ipady=10)

    return button


create_button(button_frame, "READ", read_offsets, PANEL_LIGHT)
create_button(button_frame, "SAVE", save_offsets, BLUE)


# ---------------------------------------------------------
# SHUTDOWN
# ---------------------------------------------------------


def close_application():
    if robot.ser is not None and robot.ser.is_open:
        robot.ser.close()

    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_application)

root.mainloop()
