#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ONYX-Pro Firmware Builder: compile RP2040 UF2 into a ZIP and create SHA-256."""

from __future__ import annotations
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import threading
import zipfile
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_VERSION = "v0.1.3"
FQBN = "rp2040:rp2040:waveshare_rp2040_zero"
BOARD_OPTIONS = (
    "flash=2097152_0,freq=200,exceptions=Disabled,"
    "dbgport=Disabled,dbglvl=None,ipbtstack=ipv4only"
)
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def find_cli():
    found = shutil.which("arduino-cli") or shutil.which("arduino-cli.exe")
    if found:
        return found
    roots = [os.environ.get("LOCALAPPDATA"), os.environ.get("ProgramFiles"),
             os.environ.get("ProgramFiles(x86)")]
    suffixes = [
        "Programs/Arduino IDE/resources/app/lib/backend/resources/arduino-cli.exe",
        "Programs/Arduino IDE/resources/app/lib/backend/arduino-cli.exe",
        "Arduino IDE/resources/app/lib/backend/resources/arduino-cli.exe",
        "Arduino IDE/resources/app/lib/backend/arduino-cli.exe",
    ]
    for root in filter(None, roots):
        for suffix in suffixes:
            candidate = Path(root) / suffix
            if candidate.is_file():
                return str(candidate)
    return ""


class App:
    def __init__(self, root):
        self.root = root
        root.title(f"ONYX-Pro Firmware Builder {APP_VERSION}")
        root.geometry("820x680")
        root.minsize(740, 600)
        self.sketch = tk.StringVar()
        self.output = tk.StringVar()
        self.version = tk.StringVar(value="1.1.0")
        self.cli = tk.StringVar(value=find_cli())
        self.installation_guide = tk.StringVar(
            value=str(Path(__file__).resolve().with_name("INSTALLATION_GUIDE.txt"))
        )
        self.include_installation_guide = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Listo. Seleccioná el firmware y la carpeta de salida.")
        self.building = False
        self.ui()

    def ui(self):
        # Dark graphite theme with restrained ONYX-blue accents.
        self.root.configure(bg="#17191d")
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        bg = "#17191d"
        panel = "#22252b"
        panel_alt = "#292d35"
        fg = "#e7eaf0"
        muted = "#aab2c0"
        accent = "#2388e8"
        accent_active = "#1474ce"
        border = "#3a404b"

        style.configure(".", background=bg, foreground=fg, font=("Segoe UI", 9))
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TLabelframe", background=bg, foreground=fg, bordercolor=border)
        style.configure("TLabelframe.Label", background=bg, foreground="#75baff",
                        font=("Segoe UI", 9, "bold"))
        style.configure("TEntry", fieldbackground=panel_alt, foreground=fg,
                        insertcolor=fg, bordercolor=border, lightcolor=border,
                        darkcolor=border, padding=6)
        style.map("TEntry", fieldbackground=[("disabled", panel)],
                  foreground=[("disabled", muted)])
        style.configure("TButton", background=panel_alt, foreground=fg,
                        bordercolor=border, padding=(10, 6), focusthickness=0)
        style.map("TButton",
                  background=[("active", "#363c47"), ("pressed", "#303640"),
                              ("disabled", panel)],
                  foreground=[("disabled", muted)])
        style.configure("TScrollbar", background=panel_alt, troughcolor=bg,
                        bordercolor=bg, arrowcolor=fg)
        style.configure("TSeparator", background=border)

        outer = ttk.Frame(self.root, padding=15)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="ONYX-Pro", font=("Segoe UI", 20, "bold"),
                  foreground="#75baff").pack(anchor="w")
        ttk.Label(outer, text="Firmware Builder | Waveshare RP2040 Zero | Arduino-Pico").pack(anchor="w", pady=(0, 12))

        box = ttk.LabelFrame(outer, text="Configuración", padding=10)
        box.pack(fill="x")
        box.columnconfigure(1, weight=1)
        rows = [
            ("Carpeta del firmware:", self.sketch, self.pick_sketch),
            ("Carpeta de salida:", self.output, self.pick_output),
            ("Arduino CLI:", self.cli, self.pick_cli),
        ]
        for i, (label, var, cmd) in enumerate(rows):
            ttk.Label(box, text=label).grid(row=i, column=0, sticky="w", pady=5)
            ttk.Entry(box, textvariable=var).grid(row=i, column=1, sticky="ew", padx=8)
            ttk.Button(box, text="Examinar…", command=cmd).grid(row=i, column=2)
        ttk.Label(box, text="Versión pública:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(box, textvariable=self.version, width=18).grid(row=3, column=1, sticky="w", padx=8)
        ttk.Label(box, text="SemVer: MAJOR.MINOR.PATCH").grid(row=3, column=1, sticky="e", padx=8)

        guide_box = ttk.LabelFrame(outer, text="Documentación de instalación", padding=10)
        guide_box.pack(fill="x", pady=(10, 0))
        guide_box.columnconfigure(1, weight=1)
        ttk.Checkbutton(
            guide_box,
            text="Incluir INSTALLATION_GUIDE.txt dentro del ZIP",
            variable=self.include_installation_guide,
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        ttk.Label(guide_box, text="Archivo:").grid(row=1, column=0, sticky="w")
        ttk.Entry(guide_box, textvariable=self.installation_guide).grid(
            row=1, column=1, sticky="ew", padx=8
        )
        ttk.Button(guide_box, text="Examinar…", command=self.pick_installation_guide).grid(
            row=1, column=2
        )

        board = ttk.LabelFrame(outer, text="Perfil de compilación (bloqueado)", padding=10)
        board.pack(fill="x", pady=10)
        vals = [
            ("Placa", "Waveshare RP2040 Zero"),
            ("Core", "Arduino-Pico by Earle Philhower"),
            ("Flash", "2MB (no FS)"),
            ("CPU", "200 MHz"),
            ("Debug", "Level None / Port Disabled"),
            ("C++ Exceptions", "Disabled"),
            ("IP/Bluetooth", "IPv4 Only"),
        ]
        for i, (k, v) in enumerate(vals):
            ttk.Label(board, text=f"{k}:").grid(row=i // 2, column=(i % 2) * 2, sticky="w", padx=(0, 5), pady=2)
            ttk.Label(board, text=v, font=("Segoe UI", 9, "bold")).grid(row=i // 2, column=(i % 2) * 2 + 1, sticky="w", padx=(0, 18), pady=2)

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(0, 8))
        self.btn = ttk.Button(actions, text="▶  COMPILAR Y CREAR RELEASE", command=self.start)
        self.btn.pack(side="left")
        ttk.Button(actions, text="Limpiar registro", command=self.clear).pack(side="right")

        lf = ttk.LabelFrame(outer, text="Registro del proceso", padding=7)
        lf.pack(fill="both", expand=True)
        self.log = tk.Text(
            lf, wrap="word", state="disabled", font=("Consolas", 9),
            bg="#111317", fg="#dce3ed", insertbackground="#ffffff",
            selectbackground="#245b91", selectforeground="#ffffff",
            relief="flat", borderwidth=0, padx=9, pady=8
        )
        sb = ttk.Scrollbar(lf, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        ttk.Label(outer, textvariable=self.status).pack(anchor="w", pady=(7, 0))

    def pick_sketch(self):
        p = filedialog.askdirectory(title="Seleccionar carpeta del firmware RP2040")
        if p:
            self.sketch.set(p)
            if not self.output.get():
                self.output.set(str(Path(p).parent / "Firmware_Releases"))

    def pick_output(self):
        p = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if p:
            self.output.set(p)

    def pick_cli(self):
        p = filedialog.askopenfilename(title="Seleccionar arduino-cli.exe",
                                       filetypes=[("Arduino CLI", "arduino-cli.exe"), ("Todos", "*.*")])
        if p:
            self.cli.set(p)

    def pick_installation_guide(self):
        p = filedialog.askopenfilename(
            title="Seleccionar INSTALLATION_GUIDE.txt",
            filetypes=[("Archivo de texto", "*.txt"), ("Todos", "*.*")],
        )
        if p:
            self.installation_guide.set(p)

    def log_line(self, text):
        def add():
            self.log.configure(state="normal")
            self.log.insert("end", str(text).rstrip() + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        self.root.after(0, add)

    def status_line(self, text):
        self.root.after(0, lambda: self.status.set(text))

    def clear(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.status.set("Registro limpio. No se borró ningún archivo.")

    def start(self):
        sketch = Path(self.sketch.get().strip()).expanduser()
        output = Path(self.output.get().strip()).expanduser()
        version = self.version.get().strip()
        cli = self.cli.get().strip() or find_cli()
        include_guide = self.include_installation_guide.get()
        guide = Path(self.installation_guide.get().strip()).expanduser() if self.installation_guide.get().strip() else None
        if not sketch.is_dir():
            messagebox.showwarning("ONYX-Pro", "Seleccioná una carpeta de firmware válida.")
            return
        if not output:
            messagebox.showwarning("ONYX-Pro", "Seleccioná la carpeta de salida.")
            return
        if not re.fullmatch(r"\d+\.\d+\.\d+", version):
            messagebox.showwarning("ONYX-Pro", "Usá formato SemVer, por ejemplo 1.1.0.")
            return
        if not cli or not Path(cli).is_file():
            messagebox.showerror("ONYX-Pro", "No encuentro arduino-cli. Seleccioná arduino-cli.exe con «Examinar…».")
            return
        if include_guide and (guide is None or not guide.is_file()):
            messagebox.showerror(
                "ONYX-Pro",
                "La opción de incluir la guía está activada, pero no se encuentra INSTALLATION_GUIDE.txt.\n\n"
                "Seleccioná el archivo con «Examinar…» o desactivá la opción.",
            )
            return
        ino = list(sketch.glob("*.ino"))
        if len(ino) != 1:
            messagebox.showerror("ONYX-Pro", "La carpeta seleccionada debe contener exactamente un archivo .ino en su raíz.")
            return
        output.mkdir(parents=True, exist_ok=True)
        base = f"ONYX-Pro_Firmware_v{version}"
        # Only the ZIP package and its checksum are published as output files.
        targets = [output / f"{base}.zip", output / f"{base}.zip.sha256"]
        existing = [p.name for p in targets if p.exists()]
        if existing and not messagebox.askyesno("ONYX-Pro", "Ya existen estos archivos:\n\n" + "\n".join(existing) + "\n\n¿Reemplazarlos?"):
            return
        self.cli.set(cli)
        self.btn.configure(state="disabled")
        self.status_line("Compilando firmware…")
        self.log_line("=" * 65)
        self.log_line(f"ONYX-Pro Firmware Builder {APP_VERSION}")
        self.log_line(f"Fecha: {datetime.now().astimezone().isoformat(timespec='seconds')}")
        self.log_line(f"Sketch: {sketch}")
        self.log_line(f"Versión: v{version}")
        self.log_line(f"Placa: {FQBN}")
        self.log_line(f"Opciones: {BOARD_OPTIONS}")
        self.log_line(f"Guía de instalación incluida: {'Sí' if include_guide else 'No'}")
        if include_guide:
            self.log_line(f"Guía: {guide}")
        self.log_line("El código fuente no se modifica.")
        threading.Thread(
            target=self.worker,
            args=(cli, sketch, output, base, version, guide if include_guide else None),
            daemon=True,
        ).start()

    def worker(self, cli, sketch, output, base, version, guide):
        try:
            with tempfile.TemporaryDirectory(prefix="onyx_firmware_") as tmp:
                build = Path(tmp) / "build"
                build.mkdir()
                cmd = [cli, "compile", "--fqbn", FQBN, "--board-options", BOARD_OPTIONS,
                       "--clean", "--output-dir", str(build), str(sketch)]
                self.log_line("\n[1/4] Compilando con Arduino CLI…")
                self.log_line(subprocess.list2cmdline(cmd))
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, encoding="utf-8", errors="replace", bufsize=1)
                assert proc.stdout is not None
                for line in proc.stdout:
                    self.log_line(line)
                code = proc.wait()
                if code:
                    raise RuntimeError(f"Arduino CLI terminó con código {code}. Revisá el registro.")
                uf2s = list(build.rglob("*.uf2"))
                if not uf2s:
                    raise RuntimeError("La compilación terminó, pero no se encontró ningún archivo .uf2.")
                if len(uf2s) > 1:
                    matching = [p for p in uf2s if p.stem.lower() == sketch.name.lower()]
                    if len(matching) != 1:
                        raise RuntimeError("Se generaron varios UF2 y no puedo identificar el principal.")
                    source = matching[0]
                else:
                    source = uf2s[0]

                archive_uf2_name = f"{base}.uf2"
                archive = output / f"{base}.zip"
                checksum = output / f"{base}.zip.sha256"
                self.log_line("\n[2/4] UF2 compilado (se incluirá únicamente dentro del ZIP):")
                self.log_line(f"{archive_uf2_name} ({source.stat().st_size:,} bytes)")

                readme = (
                    "ONYX-Pro RP2040 Firmware\n"
                    "========================\n"
                    f"Release: v{version}\n"
                    "Board: Waveshare RP2040 Zero\n"
                    "Core: Arduino-Pico by Earle Philhower\n"
                    f"FQBN: {FQBN}\n"
                    "Flash: 2MB (no FS) | CPU: 200 MHz\n"
                    "Debug Level: None | Debug Port: Disabled\n"
                    "C++ Exceptions: Disabled | IP/Bluetooth: IPv4 Only\n\n"
                    "Installation:\n"
                    "1. Hold BOOTSEL while connecting the RP2040 Zero by USB.\n"
                    "2. Copy the UF2 file to the RPI-RP2 drive.\n"
                    "3. Wait for the board to reboot.\n"
                )
                self.log_line("\n[3/4] Creando ZIP…")
                with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                    zf.write(source, arcname=archive_uf2_name)
                    zf.writestr("README.txt", readme)
                    if guide is not None:
                        zf.write(guide, arcname="INSTALLATION_GUIDE.txt")
                        self.log_line("Guía agregada al ZIP: INSTALLATION_GUIDE.txt")
                # Calculate the checksum only after every ZIP file has been added.
                digest = hashlib.sha256(archive.read_bytes()).hexdigest()
                checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")

                self.log_line("\n[4/4] SHA-256:")
                self.log_line(digest)
                self.log_line("\nRELEASE CREADO CORRECTAMENTE")
                self.log_line(str(archive))
                self.log_line(str(checksum))
                self.status_line(f"Release v{version} creado correctamente.")
                self.root.after(0, lambda: messagebox.showinfo(
                    "ONYX-Pro", f"¡Firmware compilado y empaquetado!\n\n{base}.zip\n{base}.zip.sha256"
                    + ("\nINSTALLATION_GUIDE.txt incluido en el ZIP" if guide is not None else "\nGuía de instalación no incluida")
                    + f"\n\n{output}"
                ))
        except Exception as exc:
            self.log_line(f"\nERROR: {exc}")
            self.status_line("Proceso interrumpido. Revisá el registro.")
            self.root.after(0, lambda msg=str(exc): messagebox.showerror("ONYX-Pro", msg))
        finally:
            self.root.after(0, lambda: self.btn.configure(state="normal"))


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
