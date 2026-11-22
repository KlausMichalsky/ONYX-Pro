

"""

ONYX-Pro Release Manager

GUI application using Tkinter.

Compatible with macOS and Windows.

"""

import re
import shutil
import tkinter as tk
from datetime import date, datetime
from pathlib import Path
from tkinter import ttk, messagebox

CATEGORIES = ("Added", "Changed", "Fixed", "Removed", "Security")

COMPONENTS = {

    "Zero": "RP2040 Firmware",

    "Raspi": "Raspberry Pi Software",

}


def find_repo_root():

    root = Path(__file__).resolve().parent.parent

    for folder in COMPONENTS:

        if not (root / folder).is_dir():

            raise FileNotFoundError(

                f"Repository folder not found: {folder}"

            )

    return root


def extract_unreleased(text):

    match = re.search(

        r"(?m)^##\s+\[Unreleased\]\s*\r?\n",

        text

    )

    if not match:

        raise ValueError("Missing [Unreleased] section.")

    next_heading = re.search(

        r"(?m)^##\s+\[[^\]]+\].*$",

        text[match.end():]

    )

    if next_heading:

        end = match.end() + next_heading.start()

        return (

            text[:match.start()],

            text[match.end():end],

            text[end:]

        )

    return text[:match.start()], text[match.end():], ""


def parse_categories(body):

    result = {category: [] for category in CATEGORIES}

    current = None

    for line in body.splitlines():

        stripped = line.strip()

        if not stripped:

            continue

        heading = re.fullmatch(r"###\s+(.+?)\s*", stripped)

        if heading:

            name = heading.group(1)

            if name not in CATEGORIES:

                raise ValueError(f"Unknown category: {name}")

            current = name

            continue

        if current is None:

            raise ValueError(

                "Unexpected content before a category heading."

            )

        if stripped in ("-", "*", "+"):

            continue

        result[current].append(line.rstrip())

    return result


def has_changes(categories):

    return any(

        line.strip() and not line.lstrip().startswith("<!--")

        for entries in categories.values()

        for line in entries

    )


def build_unreleased():

    lines = ["## [Unreleased]", ""]

    for category in CATEGORIES:

        lines.extend((f"### {category}", ""))

    return "\n".join(lines).rstrip() + "\n"


def build_release(version, release_date, categories):

    lines = [f"## [{version}] - {release_date}", ""]

    for category in CATEGORIES:

        entries = categories[category]

        if entries:

            lines.append(f"### {category}")

            lines.extend(entries)

            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


class ReleaseManager:

    def __init__(self, root):

        self.root = root

        self.window = tk.Tk()

        self.window.title("ONYX-Pro Release Manager")

        self.window.geometry("476x553")

        self.window.minsize(450, 500)

        self.component = tk.StringVar(value="Zero")

        self.version = tk.StringVar()

        self.release_date = tk.StringVar(

            value=date.today().isoformat()

        )

        self.configure_theme()

        self.create_interface()

    def configure_theme(self):

        style = ttk.Style(self.window)

        style.theme_use("clam")

        # ONYX-Pro Dark Palette
        BG = "#15171B"

        PANEL = "#202329"

        FIELD = "#292D34"

        FG = "#E6E8EB"

        MUTED = "#9299A5"

        ACCENT = "#3978D4"

        ACCENT_HOVER = "#4B8BE8"

        BORDER = "#363B44"

        self.window.configure(bg=BG)

        style.configure(

            ".",

            background=BG,

            foreground=FG,

            font=("Arial", 9)

        )

        style.configure(

            "TFrame",

            background=BG

        )

        style.configure(

            "TLabel",

            background=BG,

            foreground=FG

        )

        style.configure(

            "TRadiobutton",

            background=BG,

            foreground=FG,

            indicatorcolor=FIELD,

            padding=3

        )

        style.map(

            "TRadiobutton",

            background=[("active", BG)],

            foreground=[("active", ACCENT_HOVER)],

            indicatorcolor=[

                ("selected", ACCENT),

                ("active", FIELD)

            ]

        )

        style.configure(

            "TEntry",

            fieldbackground=FIELD,

            foreground=FG,

            insertcolor=FG,

            bordercolor=BORDER,

            padding=5

        )

        style.configure(

            "TButton",

            background=PANEL,

            foreground=FG,

            bordercolor=BORDER,

            padding=(8, 5),

            font=("Arial", 9, "bold")

        )

        style.map(

            "TButton",

            background=[

                ("active", ACCENT),

                ("pressed", ACCENT_HOVER)

            ],

            foreground=[

                ("active", "#FFFFFF")

            ]

        )

        style.configure(

            "TSeparator",

            background=BORDER

        )

        self.colors = {

            "bg": BG,

            "panel": PANEL,

            "field": FIELD,

            "fg": FG,

            "muted": MUTED,

            "accent": ACCENT,

            "border": BORDER

        }

    def create_interface(self):

        main = ttk.Frame(self.window, padding=10)

        main.pack(fill="both", expand=True)

        # HEADER
        ttk.Label(

            main,

            text="ONYX-Pro",

            font=("Arial", 16, "bold")

        ).pack(anchor="w")

        ttk.Label(

            main,

            text="RELEASE MANAGEMENT SYSTEM",

            foreground="gray"

        ).pack(anchor="w", pady=(0, 10))

        # COMPONENT SELECTION
        ttk.Label(

            main,

            text="1. Select component",

            font=("Arial", 10, "bold")

        ).pack(anchor="w")

        components_frame = ttk.Frame(main)

        components_frame.pack(fill="x", pady=2)

        for folder, description in COMPONENTS.items():

            ttk.Radiobutton(

                components_frame,

                text=f"{folder}  |  {description}",

                variable=self.component,

                value=folder,

                command=self.refresh_status

            ).pack(anchor="w", pady=1)

        ttk.Separator(main).pack(fill="x", pady=6)

        # RELEASE INFORMATION
        ttk.Label(

            main,

            text="2. Release information",

            font=("Arial", 10, "bold")

        ).pack(anchor="w")

        ttk.Label(

            main,

            text="Version (MAJOR.MINOR.PATCH)"

        ).pack(anchor="w", pady=(4, 1))

        ttk.Entry(

            main,

            textvariable=self.version,

            font=("Arial", 10)

        ).pack(fill="x")

        ttk.Label(

            main,

            text="Release date (YYYY-MM-DD)"

        ).pack(anchor="w", pady=(4, 1))

        ttk.Entry(

            main,

            textvariable=self.release_date,

            font=("Arial", 10)

        ).pack(fill="x")

        ttk.Separator(main).pack(fill="x", pady=6)

        # STATUS
        self.status_label = ttk.Label(

            main,

            text="",

            foreground="gray",

            wraplength=430

        )

        self.status_label.pack(anchor="w", pady=(0, 4))

        # ACTION BUTTONS
        ttk.Button(

            main,

            text="CHECK CHANGELOG",

            command=self.check_changelog

        ).pack(fill="x", ipady=1, pady=2)

        ttk.Button(

            main,

            text="PREVIEW RELEASE",

            command=self.preview_release

        ).pack(fill="x", ipady=1, pady=2)

        ttk.Button(

            main,

            text="CREATE RELEASE",

            command=self.create_release

        ).pack(fill="x", ipady=2, pady=(4, 2))

        # FOOTER
        ttk.Label(

            main,

            text="ONYX-Pro | Release Manager",

            foreground="gray"

        ).pack(pady=(4, 0))

        self.refresh_status()

    def get_changelog(self):

        folder = self.component.get()

        path = self.root / folder / "CHANGELOG.md"

        if not path.is_file():

            raise FileNotFoundError(

                f"CHANGELOG.md not found:\n{path}"

            )

        original = path.read_text(encoding="utf-8")

        prefix, body, suffix = extract_unreleased(original)

        categories = parse_categories(body)

        return path, original, prefix, suffix, categories

    def refresh_status(self):

        folder = self.component.get()

        path = self.root / folder / "CHANGELOG.md"

        if path.is_file():

            self.status_label.config(

                text=f"Selected: {COMPONENTS[folder]}\n"

                f"CHANGELOG: {path.relative_to(self.root)}"

            )

        else:

            self.status_label.config(

                text=f"CHANGELOG not found: {path}"

            )

    def check_changelog(self):

        try:

            path, _, _, _, categories = self.get_changelog()

            if has_changes(categories):

                count = sum(

                    len(entries)

                    for entries in categories.values()

                )

                messagebox.showinfo(

                    "CHANGELOG status",

                    f"Pending changes found!\n\n"

                    f"Component: {COMPONENTS[self.component.get()]}\n"

                    f"Entries: {count}\n"

                    f"File: {path}"

                )

            else:

                messagebox.showwarning(

                    "CHANGELOG status",

                    "[Unreleased] is empty."

                )

        except (OSError, ValueError) as error:

            messagebox.showerror("Error", str(error))

    def preview_release(self):

        try:

            _, _, _, _, categories = self.get_changelog()

            if not has_changes(categories):

                messagebox.showwarning(

                    "No changes",

                    "[Unreleased] is empty."

                )

                return

            preview = ""

            for category, entries in categories.items():

                if entries:

                    preview += f"### {category}\n"

                    preview += "\n".join(entries)

                    preview += "\n\n"

            self.show_text_window(

                "Release preview",

                preview

            )

        except (OSError, ValueError) as error:

            messagebox.showerror("Error", str(error))

    def show_text_window(self, title, content):

        preview_window = tk.Toplevel(self.window)

        preview_window.title(title)

        preview_window.geometry("560x460")

        preview_window.configure(

            bg=self.colors["bg"]

        )

        preview_window.transient(self.window)

        text_frame = tk.Frame(

            preview_window,

            bg=self.colors["bg"],

            padx=15,

            pady=15

        )

        text_frame.pack(fill="both", expand=True)

        text = tk.Text(

            text_frame,

            wrap="word",

            padx=15,

            pady=15,

            bg=self.colors["field"],

            fg=self.colors["fg"],

            insertbackground=self.colors["fg"],

            selectbackground=self.colors["accent"],

            selectforeground="#FFFFFF",

            font=("Consolas", 10),

            relief="flat",

            borderwidth=0,

            spacing1=3,

            spacing3=3

        )

        scrollbar = ttk.Scrollbar(

            text_frame,

            orient="vertical",

            command=text.yview

        )

        text.configure(

            yscrollcommand=scrollbar.set

        )

        text.pack(

            side="left",

            fill="both",

            expand=True

        )

        scrollbar.pack(

            side="right",

            fill="y"

        )

        text.insert("1.0", content)

        text.config(state="disabled")

        ttk.Button(

            preview_window,

            text="CLOSE",

            command=preview_window.destroy

        ).pack(pady=(0, 15), padx=15, anchor="e")

    def create_release(self):

        version = self.version.get().strip()

        release_date = self.release_date.get().strip()

        if not re.fullmatch(

            r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)",

            version

        ):

            messagebox.showerror(

                "Invalid version",

                "Use MAJOR.MINOR.PATCH.\nExample: 1.1.1"

            )

            return

        try:

            release_date = date.fromisoformat(

                release_date

            ).isoformat()

            path, original, prefix, suffix, categories = (

                self.get_changelog()

            )

        except (ValueError, OSError) as error:

            messagebox.showerror("Error", str(error))

            return

        if not has_changes(categories):

            messagebox.showwarning(

                "No changes",

                "[Unreleased] does not contain changes."

            )

            return

        if re.search(

            rf"(?m)^##\s+\[{re.escape(version)}\]\s+-",

            original

        ):

            messagebox.showerror(

                "Version already exists",

                f"Version {version} already exists."

            )

            return

        release = build_release(

            version,

            release_date,

            categories

        )

        # Rebuild the document with consistent Markdown spacing.
        # Keep the title/introduction, reset [Unreleased], add the release,
        # and preserve all previous release history.
        new_text = (
            prefix.rstrip()
            + "\n\n"
            + build_unreleased().rstrip()
            + "\n\n---\n\n"
            + release.rstrip()
            + (
                "\n\n" + suffix.lstrip("\r\n")
                if suffix.strip()
                else "\n"
            )
        )

        summary = (

            f"Component: {COMPONENTS[self.component.get()]}\n"

            f"Version: {version}\n"

            f"Date: {release_date}\n\n"

        )

        for category, entries in categories.items():

            if entries:

                summary += (

                    f"{category}: {len(entries)} entries\n"

                )

        summary += "\nDo you want to create this release?"

        if not messagebox.askyesno(

            "Confirm release",

            summary

        ):

            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup = path.with_name(

            f"CHANGELOG.backup_{timestamp}.md"

        )

        try:

            shutil.copy2(path, backup)

            path.write_text(

                new_text,

                encoding="utf-8",

                newline="\n"

            )

        except OSError as error:

            messagebox.showerror(

                "Save error",

                f"Could not save CHANGELOG:\n{error}"

            )

            return

        messagebox.showinfo(

            "Release created",

            f"Version {version} created successfully!\n\n"

            f"Updated:\n{path}\n\n"

            f"Backup:\n{backup}"

        )

        self.version.set("")

        self.refresh_status()


if __name__ == "__main__":

    try:

        repository = find_repo_root()

        app = ReleaseManager(repository)

        app.window.mainloop()

    except Exception as error:

        root = tk.Tk()

        root.withdraw()

        messagebox.showerror(

            "ONYX-Pro Release Manager",

            str(error)

        )
