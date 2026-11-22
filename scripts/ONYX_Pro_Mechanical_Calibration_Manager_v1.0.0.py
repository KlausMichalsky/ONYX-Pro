
"""
ONYX-Pro Mechanical Calibration Manager
Mechanical calibration GUI for RP2040-Zero.
Compatible with Windows, macOS and Linux.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path


FACTORY = {
    "offset_x": 0.0,
    "offset_y": 120.0,
    "z_steps_down": 3300,
}

LIMITS = {
    "offset_x": (-7.0, 7.0),
    "offset_y": (113.0, 127.0),
    "z_steps_down": (3000, 3600),
}

BG = "#15171B"
PANEL = "#202329"
FIELD = "#292D34"
FG = "#E6E8EB"
MUTED = "#9299A5"
ACCENT = "#3978D4"
HOVER = "#4B8BE8"
BORDER = "#363B44"


class CalibrationManager:

    def __init__(self):

        self.root = tk.Tk()
        self.root.title("ONYX-Pro Mechanical Calibration")
        self.root.geometry("520x610")
        self.root.minsize(500, 570)
        self.root.configure(bg=BG)

        self.vars = {
            "offset_x": tk.StringVar(value="0.0"),
            "offset_y": tk.StringVar(value="120.0"),
            "z_steps_down": tk.StringVar(value="3300"),
        }

        self.status = tk.StringVar(
            value="Factory calibration values loaded."
        )

        self.configure_theme()
        self.create_interface()

    def configure_theme(self):

        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(
            ".",
            background=BG,
            foreground=FG,
            font=("Arial", 10)
        )

        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("Muted.TLabel", background=BG, foreground=MUTED)
        style.configure("Panel.TLabel", background=PANEL, foreground=FG)

        style.configure(
            "TEntry",
            fieldbackground=FIELD,
            foreground=FG,
            insertcolor=FG,
            bordercolor=BORDER,
            padding=8
        )

        style.configure(
            "TButton",
            background=PANEL,
            foreground=FG,
            bordercolor=BORDER,
            padding=(12, 9),
            font=("Arial", 10, "bold")
        )

        style.map(
            "TButton",
            background=[
                ("active", ACCENT),
                ("pressed", HOVER)
            ],
            foreground=[("active", "#FFFFFF")]
        )

        style.configure(
            "Accent.TButton",
            background=ACCENT,
            foreground="#FFFFFF"
        )

        style.map(
            "Accent.TButton",
            background=[
                ("active", HOVER),
                ("pressed", ACCENT)
            ]
        )

    def add_parameter(
        self, parent, row, key, title, description, allowed
    ):

        ttk.Label(
            parent,
            text=title,
            style="Panel.TLabel",
            font=("Arial", 10, "bold")
        ).grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w"
        )

        ttk.Label(
            parent,
            text=description,
            style="Panel.TLabel",
            wraplength=315
        ).grid(
            row=row + 1,
            column=0,
            sticky="w",
            pady=(3, 5)
        )

        ttk.Entry(
            parent,
            textvariable=self.vars[key],
            width=13,
            justify="right"
        ).grid(
            row=row + 1,
            column=1,
            sticky="e",
            padx=(10, 0)
        )

        ttk.Label(
            parent,
            text=f"Factory: {FACTORY[key]}   |   Allowed: {allowed}",
            style="Panel.TLabel",
            font=("Arial", 8)
        ).grid(
            row=row + 2,
            column=0,
            columnspan=2,
            sticky="w"
        )

        parent.grid_columnconfigure(0, weight=1)

    def create_interface(self):

        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text="ONYX-Pro",
            font=("Arial", 19, "bold")
        ).pack(anchor="w")

        ttk.Label(
            main,
            text="MECHANICAL CALIBRATION",
            style="Muted.TLabel"
        ).pack(anchor="w", pady=(0, 12))

        panel = ttk.Frame(
            main,
            style="Panel.TFrame",
            padding=14
        )
        panel.pack(fill="x")

        self.add_parameter(
            panel,
            0,
            "offset_x",
            "OFFSET_X  |  X-Axis calibration (mm)",
            "Relative correction added to the nominal X position of the chessboard. Defines the horizontal displacement along the X-axis, in millimeters (mm)",
            "-10.0 to +10.0 mm"
        )

        ttk.Separator(panel).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=10
        )

        self.add_parameter(
            panel,
            4,
            "offset_y",
            "OFFSET_Y  |  Y- reference (mm)",
            "Distance along the Y-axis from the mechanical origin to the center of the first row of the chessboard, measured in millimeters (mm)",
            "113.0 to 127.0 mm"
        )

        ttk.Separator(panel).grid(
            row=7,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=10
        )

        self.add_parameter(
            panel,
            8,
            "z_steps_down",
            "Z_STEPS_DOWN  |  Grip depth (steps)",
            "Steps from the Z sensor to the lowest grip position.",
            "3000 to 3600 steps"
        )

        ttk.Label(
            main,
            text=(
                "Z calibration is sensitive. Changes from "
                "3300 steps trigger a warning."
            ),
            style="Muted.TLabel",
            wraplength=455
        ).pack(anchor="w", pady=(12, 8))

        ttk.Separator(main).pack(fill="x", pady=8)

        buttons = ttk.Frame(main)
        buttons.pack(fill="x")

        ttk.Button(
            buttons,
            text="RESTORE FACTORY DEFAULTS",
            command=self.restore_defaults
        ).pack(side="left")

        ttk.Button(
            buttons,
            text="GENERATE userconfig.h",
            style="Accent.TButton",
            command=self.generate_header
        ).pack(side="right")

        ttk.Label(
            main,
            textvariable=self.status,
            style="Muted.TLabel",
            wraplength=455
        ).pack(anchor="w", pady=(12, 0))

        ttk.Label(
            main,
            text="ONYX-Pro  |  RP2040-Zero",
            style="Muted.TLabel"
        ).pack(side="bottom", pady=(12, 0))

    def read_values(self):

        values = {}

        for key, variable in self.vars.items():

            try:
                value = float(
                    variable.get().strip().replace(",", ".")
                )
            except ValueError:
                raise ValueError(
                    f"Invalid value for {key.upper()}."
                )

            low, high = LIMITS[key]

            if not low <= value <= high:
                raise ValueError(
                    f"{key.upper()} must be between {low} and {high}."
                )

            if key == "z_steps_down" and not value.is_integer():
                raise ValueError(
                    "Z_STEPS_DOWN must be a whole number of steps."
                )

            values[key] = (
                int(value)
                if key == "z_steps_down"
                else value
            )

        return values

    def restore_defaults(self):

        for key, value in FACTORY.items():
            self.vars[key].set(str(value))

        self.status.set(
            "Factory defaults restored. No file has been written."
        )

    def build_header(self, values):

        return f"""// =======================================================================
// ONYX-Pro | Mechanical Calibration
// Generated by ONYX-Pro Mechanical Calibration Manager
// =======================================================================

#pragma once

// Relative correction added to the nominal X formula.
// Factory: 0.0 mm | Allowed: -10.0 to +10.0 mm
constexpr float USER_OFFSET_X_CORRECTION = {values["offset_x"]:.1f}f;

// Absolute Y reference from the mechanical origin.
// Factory: 121.0 mm | Allowed: 111.0 to 131.0 mm
constexpr float USER_OFFSET_Y = {values["offset_y"]:.1f}f;

// Steps from the Z sensor to the lowest grip position.
// Factory: 3300 | Allowed: 3000 to 3600
constexpr long USER_Z_STEPS_DOWN = {values["z_steps_down"]};
"""

    def generate_header(self):

        try:
            values = self.read_values()
        except ValueError as error:
            messagebox.showerror(
                "Invalid calibration",
                str(error),
                parent=self.root
            )
            return

        if values["z_steps_down"] != FACTORY["z_steps_down"]:

            proceed = messagebox.askyesno(
                "Sensitive Z calibration",
                "Z_STEPS_DOWN differs from the factory value "
                "of 3300 steps.\n\n"
                "An excessive downward movement can press hard "
                "against a chess piece.\n\n"
                "Confirm that this value was calibrated carefully.\n\n"
                "Continue?",
                parent=self.root
            )

            if not proceed:
                return

        filename = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save mechanical calibration",
            initialfile="userconfig.h",
            defaultextension=".h",
            filetypes=[
                ("C/C++ header", "*.h"),
                ("All files", "*.*")
            ]
        )

        if not filename:
            return

        path = Path(filename)

        try:
            path.write_text(
                self.build_header(values),
                encoding="utf-8",
                newline="\n"
            )
        except OSError as error:
            messagebox.showerror(
                "Save error",
                str(error),
                parent=self.root
            )
            return

        self.status.set(f"Generated: {path}")

        messagebox.showinfo(
            "Calibration generated",
            f"userconfig.h was generated successfully:\n\n{path}\n\n"
            "The firmware must include and validate these values "
            "before they control the motors.",
            parent=self.root
        )

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    CalibrationManager().run()
