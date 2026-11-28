import tkinter as tk

# =========================================================
# ONYX-Pro HOME SCREEN
# =========================================================

BG = "#10151D"
PANEL = "#1C2633"

BLUE = "#168BE1"
BLUE_HOVER = "#269FF5"

TEXT = "#E8EDF5"
MUTED = "#8292A7"
BORDER = "#344154"


class HomeScreen:

    def __init__(self, parent, app):

        self.parent = parent
        self.app = app

        self.frame = tk.Frame(parent, bg=BG)

        self.frame.pack(fill="both", expand=True)

        self.build_header()
        self.build_welcome()
        self.build_start_button()
        self.build_secondary_buttons()

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    def build_header(self):

        header = tk.Frame(self.frame, bg=BG)

        header.pack(fill="x", padx=28, pady=(20, 8))

        branding = tk.Frame(header, bg=BG)

        branding.pack(side="left")

        tk.Label(
            branding, text="ONYX-Pro", font=("Arial", 25, "bold"), bg=BG, fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            branding,
            text="AUTONOMOUS CHESS ROBOT",
            font=("Arial", 8, "bold"),
            bg=BG,
            fg=MUTED,
        ).pack(anchor="w")

        self.app.create_power_button(header)

        tk.Frame(self.frame, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(8, 0))

    # -----------------------------------------------------
    # WELCOME
    # -----------------------------------------------------

    def build_welcome(self):

        welcome = tk.Frame(self.frame, bg=BG)

        welcome.pack(fill="x", pady=(15, 12))

        tk.Label(
            welcome, text="LET'S PLAY CHESS", font=("Arial", 22, "bold"), bg=BG, fg=TEXT
        ).pack()

        tk.Label(
            welcome,
            text="YOUR INTELLIGENT CHESS COMPANION",
            font=("Arial", 9),
            bg=BG,
            fg=MUTED,
        ).pack(pady=(4, 0))

    # -----------------------------------------------------
    # START GAME
    # -----------------------------------------------------

    def build_start_button(self):

        button_frame = tk.Frame(self.frame, bg=BG)

        button_frame.pack(fill="x", padx=65, pady=(5, 13))

        button = tk.Button(
            button_frame,
            text="♞    START GAME",
            font=("Arial", 19, "bold"),
            bg="#123D67",
            fg="white",
            activebackground=BLUE_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=lambda: self.app.show_screen("start"),
        )

        button.pack(fill="x", ipady=17)

    # -----------------------------------------------------
    # SECONDARY BUTTONS
    # -----------------------------------------------------

    def build_secondary_buttons(self):

        buttons = tk.Frame(self.frame, bg=BG)

        buttons.pack(fill="x", padx=65, pady=(0, 12))

        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)

        self.create_menu_button(
            buttons, "⚙   CALIBRATION", 0, lambda: self.app.show_screen("calibration")
        )

        self.create_menu_button(
            buttons, "⚙   SETTINGS", 1, lambda: self.app.show_screen("settings")
        )

    def create_menu_button(self, parent, text, column, command):

        button = tk.Button(
            parent,
            text=text,
            font=("Arial", 11, "bold"),
            bg=PANEL,
            fg=TEXT,
            activebackground=BLUE,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=command,
        )

        button.grid(row=0, column=column, sticky="nsew", padx=6, ipady=15)
