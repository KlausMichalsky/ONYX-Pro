import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import sys
import math

# ---------------------------------------------------------
# ONYX-Pro GUI
# Tkinter Interface Test
# ---------------------------------------------------------

RASPI_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RASPI_DIR))

import robot

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


# ---------------------------------------------------------
# WINDOW
# ---------------------------------------------------------

root = tk.Tk()
root.title("ONYX-Pro | Machine Calibration")
root.geometry("800x480")
root.resizable(False, False)
root.configure(bg=BG)


# ---------------------------------------------------------
# CONNECTION STATUS
# ---------------------------------------------------------

connection_status = tk.StringVar(value="DISCONNECTED")
status_color = tk.StringVar(value=MUTED)


def update_status(text, color):
    connection_status.set(text)
    status_label.configure(fg=color)
    root.update_idletasks()


def ensure_connection():
    if robot.ser is None or not robot.ser.is_open:
        update_status("CONNECTING...", BLUE)
        robot.initialize_serial()

    return True


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

separator = tk.Frame(root, bg=BORDER, height=1)
separator.pack(fill="x", padx=28, pady=8)


# ---------------------------------------------------------
# MAIN CONTENT
# ---------------------------------------------------------

main = tk.Frame(root, bg=BG)
main.pack(fill="both", expand=True, padx=28, pady=10)

title = tk.Label(
    main, text="MACHINE CALIBRATION", font=("Arial", 19, "bold"), bg=BG, fg=TEXT
)
title.pack(anchor="w")

description = tk.Label(
    main, text="XY coordinate offsets", font=("Arial", 10), bg=BG, fg=MUTED
)
description.pack(anchor="w", pady=(2, 15))


# ---------------------------------------------------------
# OFFSET INPUTS
# ---------------------------------------------------------

offset_frame = tk.Frame(main, bg=BG)
offset_frame.pack(fill="x")

offset_frame.columnconfigure(0, weight=1)
offset_frame.columnconfigure(1, weight=1)


def create_offset_panel(parent, column, label, default):
    panel = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)

    panel.grid(
        row=0, column=column, sticky="nsew", padx=(0, 8) if column == 0 else (8, 0)
    )

    tk.Label(panel, text=label, font=("Arial", 10, "bold"), bg=PANEL, fg=MUTED).pack(
        anchor="w", padx=18, pady=(13, 5)
    )

    entry = tk.Entry(
        panel,
        font=("Arial", 25, "bold"),
        bg=PANEL_LIGHT,
        fg="#60A5FA",
        insertbackground=TEXT,
        relief="flat",
        justify="center",
        bd=0,
    )

    entry.insert(0, default)
    entry.pack(fill="x", padx=18, pady=(0, 8), ipady=7)

    tk.Label(
        panel, text="MILLIMETERS", font=("Arial", 8, "bold"), bg=PANEL, fg=MUTED
    ).pack(anchor="w", padx=18, pady=(0, 12))

    return entry


offset_x_entry = create_offset_panel(offset_frame, 0, "OFFSET X", "-140.00")

offset_y_entry = create_offset_panel(offset_frame, 1, "OFFSET Y", "120.00")


# ---------------------------------------------------------
# BUTTONS
# ---------------------------------------------------------

button_frame = tk.Frame(main, bg=BG)
button_frame.pack(fill="x", pady=18)


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


# ---------------------------------------------------------
# READ OFFSETS
# ---------------------------------------------------------


def read_offsets():
    try:
        update_status("CONNECTING...", BLUE)
        ensure_connection()

        update_status("READING...", BLUE)

        x, y = robot.get_offsets()

        offset_x_entry.delete(0, tk.END)
        offset_x_entry.insert(0, f"{x:.2f}")

        offset_y_entry.delete(0, tk.END)
        offset_y_entry.insert(0, f"{y:.2f}")

        update_status("CONNECTED", GREEN)

    except Exception as error:
        update_status("CONNECTION ERROR", RED)

        messagebox.showerror("ONYX-Pro", f"Could not read offsets:\n\n{error}")


# ---------------------------------------------------------
# SAVE OFFSETS
# ---------------------------------------------------------


def save_offsets():
    try:
        x = float(offset_x_entry.get())
        y = float(offset_y_entry.get())

        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError("Values must be finite numbers.")

        update_status("CONNECTING...", BLUE)
        ensure_connection()

        update_status("SENDING...", BLUE)

        success = robot.set_offsets(x, y)

        if not success:
            raise RuntimeError("RP2040 did not confirm the offsets.")

        # Verify the values directly from the RP2040
        actual_x, actual_y = robot.get_offsets()

        offset_x_entry.delete(0, tk.END)
        offset_x_entry.insert(0, f"{actual_x:.2f}")

        offset_y_entry.delete(0, tk.END)
        offset_y_entry.insert(0, f"{actual_y:.2f}")

        update_status("CONNECTED", GREEN)

        messagebox.showinfo("ONYX-Pro", "Offsets updated successfully!")

    except ValueError as error:
        update_status("INVALID INPUT", RED)

        messagebox.showwarning("Invalid values", str(error))

    except Exception as error:
        update_status("CONNECTION ERROR", RED)

        messagebox.showerror("ONYX-Pro", f"Could not update offsets:\n\n{error}")


read_button = create_button(button_frame, "READ", read_offsets, "#174A7A")

save_button = create_button(button_frame, "SAVE", save_offsets, BLUE)


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

footer = tk.Frame(root, bg=BG)
footer.pack(fill="x", padx=28, pady=(0, 15))

tk.Label(
    footer,
    text="RP2040  |  USB SERIAL  |  115200 BAUD",
    font=("Arial", 8, "bold"),
    bg=BG,
    fg=MUTED,
).pack(side="left")

tk.Label(footer, text="ONYX-Pro", font=("Arial", 8, "bold"), bg=BG, fg=BLUE).pack(
    side="right"
)


# ---------------------------------------------------------
# CLOSE APPLICATION
# ---------------------------------------------------------


def close_application():
    try:
        if robot.ser is not None and robot.ser.is_open:
            robot.ser.close()
    except Exception:
        pass

    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_application)


# ---------------------------------------------------------
# START GUI
# ---------------------------------------------------------

root.mainloop()
