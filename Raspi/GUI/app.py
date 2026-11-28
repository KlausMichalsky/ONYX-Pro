import tkinter as tk
from tkinter import messagebox
import subprocess

from home_screen import HomeScreen

# =========================================================
# ONYX-Pro GUI
# Main Application Controller
# =========================================================

# COLORS
BG = "#10151D"
PANEL = "#1C2633"
PANEL_LIGHT = "#253344"

BLUE = "#168BE1"
BLUE_HOVER = "#269FF5"

TEXT = "#E8EDF5"
MUTED = "#8292A7"

GREEN = "#38C98A"
YELLOW = "#F5C451"
RED = "#F06464"
GRAY = "#8292A7"

BORDER = "#344154"


class OnyxApp:

    def __init__(self, root):

        self.root = root

        self.root.title("ONYX-Pro")
        self.root.geometry("800x480")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.selected_color = None
        self.current_screen = None

        # Main screen container
        self.container = tk.Frame(root, bg=BG)
        self.container.pack(fill="both", expand=True)

        # Persistent status bar
        self.status_bar = tk.Frame(root, bg=BG)
        self.status_bar.pack(fill="x", side="bottom", padx=24, pady=(0, 12))

        tk.Frame(root, bg=BORDER, height=1).pack(fill="x", side="bottom", padx=24)

        self.status_indicator = tk.Label(
            self.status_bar, text="●", font=("Arial", 12, "bold"), bg=BG, fg=GRAY
        )
        self.status_indicator.pack(side="left")

        self.status_label = tk.Label(
            self.status_bar,
            text="SYSTEM IDLE",
            font=("Arial", 9, "bold"),
            bg=BG,
            fg=GRAY,
        )
        self.status_label.pack(side="left", padx=(7, 0))

        self.status_detail = tk.Label(
            self.status_bar,
            text="ROBOT NOT INITIALIZED",
            font=("Arial", 8),
            bg=BG,
            fg=MUTED,
        )
        self.status_detail.pack(side="right")

        # Start at Home
        self.show_home()

    # -----------------------------------------------------
    # SCREEN MANAGEMENT
    # -----------------------------------------------------

    def clear_screen(self):

        for widget in self.container.winfo_children():
            widget.destroy()

    def show_home(self):

        self.clear_screen()
        self.current_screen = "home"

        HomeScreen(self.container, self)

    def show_screen(self, name):

        self.clear_screen()
        self.current_screen = name

        if name == "start":
            self.show_color_selection()

        elif name == "calibration":
            self.show_placeholder(
                "MACHINE CALIBRATION",
                "Calibration tools will be integrated here.",
                "HOME",
            )

        elif name == "settings":
            self.show_placeholder(
                "SETTINGS",
                "System and game preferences will be configured here.",
                "HOME",
            )

    # -----------------------------------------------------
    # COLOR SELECTION
    # -----------------------------------------------------

    def show_color_selection(self):

        self.clear_screen()
        self.current_screen = "color_selection"

        header = self.create_header("NEW GAME", self.show_home)

        tk.Label(
            self.container,
            text="SELECT YOUR COLOR",
            font=("Arial", 21, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack(pady=(30, 5))

        tk.Label(
            self.container,
            text="Choose the side you want to play",
            font=("Arial", 10),
            bg=BG,
            fg=MUTED,
        ).pack(pady=(0, 22))

        choices = tk.Frame(self.container, bg=BG)
        choices.pack(fill="x", padx=100)

        choices.columnconfigure(0, weight=1)
        choices.columnconfigure(1, weight=1)

        self.create_color_button(choices, "WHITE", "♔", 0, "#E8EDF5", "#202A38")

        self.create_color_button(choices, "BLACK", "♚", 1, PANEL_LIGHT, TEXT)

    def create_color_button(
        self, parent, color_name, symbol, column, background, foreground
    ):

        button = tk.Button(
            parent,
            text=f"{symbol}\n\n{color_name}",
            font=("Arial", 19, "bold"),
            bg=background,
            fg=foreground,
            activebackground=BLUE_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=lambda: self.select_color(color_name),
        )

        button.grid(row=0, column=column, sticky="nsew", padx=10, ipady=22)

    def select_color(self, color):

        self.selected_color = color

        # UI test only.
        # No serial communication or homing here yet.

        self.clear_screen()
        self.current_screen = "game_preview"

        self.create_header("GAME SETUP", self.show_color_selection)

        tk.Label(
            self.container,
            text=f"{color} SELECTED",
            font=("Arial", 24, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack(pady=(55, 12))

        tk.Label(
            self.container,
            text="Game initialization will be integrated next.",
            font=("Arial", 11),
            bg=BG,
            fg=MUTED,
        ).pack()

        tk.Label(
            self.container,
            text="No motors or robot movements are activated.",
            font=("Arial", 9),
            bg=BG,
            fg=YELLOW,
        ).pack(pady=12)

        self.create_action_button(
            self.container, "BACK", self.show_color_selection, PANEL_LIGHT
        )

    # -----------------------------------------------------
    # GENERIC PAGE
    # -----------------------------------------------------

    def show_placeholder(self, title, description, back_label):

        self.create_header(title, self.show_home)

        tk.Label(
            self.container, text=title, font=("Arial", 21, "bold"), bg=BG, fg=TEXT
        ).pack(pady=(65, 12))

        tk.Label(
            self.container, text=description, font=("Arial", 10), bg=BG, fg=MUTED
        ).pack()

        self.create_action_button(
            self.container, f"← {back_label}", self.show_home, PANEL_LIGHT
        )

    # -----------------------------------------------------
    # SHARED UI COMPONENTS
    # -----------------------------------------------------

    def create_header(self, title, back_command):

        header = tk.Frame(self.container, bg=BG)
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
            command=back_command,
        )
        back_button.pack(side="left", padx=(0, 14))

        tk.Label(header, text=title, font=("Arial", 15, "bold"), bg=BG, fg=TEXT).pack(
            side="left", pady=7
        )

        self.create_power_button(header)

    def create_action_button(self, parent, text, command, color=BLUE):

        button = tk.Button(
            parent,
            text=text,
            font=("Arial", 11, "bold"),
            bg=color,
            fg="white",
            activebackground=BLUE_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            command=command,
        )

        button.pack(pady=25, ipadx=35, ipady=10)

    # -----------------------------------------------------
    # POWER MENU
    # -----------------------------------------------------

    def create_power_button(self, parent):

        button = tk.Button(
            parent,
            text="⏻",
            font=("Arial", 19, "bold"),
            bg=BG,
            fg=MUTED,
            activebackground=PANEL,
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            width=3,
            command=self.show_power_menu,
        )

        button.pack(side="right")

    def show_power_menu(self):

        dialog = tk.Toplevel(self.root)
        dialog.title("ONYX-Pro Power")
        dialog.geometry("310x190")
        dialog.resizable(False, False)
        dialog.configure(bg=PANEL)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog, text="POWER OPTIONS", font=("Arial", 14, "bold"), bg=PANEL, fg=TEXT
        ).pack(pady=(18, 12))

        tk.Button(
            dialog,
            text="SHUTDOWN",
            font=("Arial", 10, "bold"),
            bg=RED,
            fg="white",
            relief="flat",
            command=lambda: self.confirm_power(dialog, "shutdown"),
        ).pack(fill="x", padx=35, pady=5, ipady=7)

        tk.Button(
            dialog,
            text="RESTART",
            font=("Arial", 10, "bold"),
            bg=PANEL_LIGHT,
            fg=TEXT,
            relief="flat",
            command=lambda: self.confirm_power(dialog, "restart"),
        ).pack(fill="x", padx=35, pady=5, ipady=7)

        tk.Button(
            dialog,
            text="CANCEL",
            font=("Arial", 9, "bold"),
            bg=PANEL,
            fg=MUTED,
            relief="flat",
            command=dialog.destroy,
        ).pack(pady=5)

    def confirm_power(self, dialog, action):

        dialog.grab_release()
        dialog.destroy()

        label = "shut down" if action == "shutdown" else "restart"

        if messagebox.askyesno(
            "ONYX-Pro", f"Are you sure you want to {label} ONYX-Pro?"
        ):

            command = (
                ["sudo", "/usr/sbin/shutdown", "-h", "now"]
                if action == "shutdown"
                else ["sudo", "/usr/sbin/shutdown", "-r", "now"]
            )

            try:
                subprocess.Popen(command)
            except Exception as error:
                messagebox.showerror("Power error", str(error))

    # -----------------------------------------------------
    # STATUS MANAGEMENT
    # -----------------------------------------------------

    def set_status(self, status, detail=""):

        states = {
            "READY": (GREEN, "SYSTEM READY"),
            "WARNING": (YELLOW, "WARNING"),
            "ERROR": (RED, "SYSTEM ERROR"),
            "BUSY": (BLUE, "SYSTEM BUSY"),
            "IDLE": (GRAY, "SYSTEM IDLE"),
        }

        color, label = states.get(status, (GRAY, "SYSTEM IDLE"))

        self.status_indicator.configure(fg=color)
        self.status_label.configure(text=label, fg=color)

        self.status_detail.configure(text=detail)


# =========================================================
# APPLICATION START
# =========================================================

if __name__ == "__main__":

    root = tk.Tk()
    app = OnyxApp(root)

    app.set_status("IDLE", "ROBOT NOT INITIALIZED")

    root.mainloop()
