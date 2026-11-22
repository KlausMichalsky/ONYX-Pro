#!/usr/bin/env python3
# ONYX-Pro Image Builder v0.4.4
# GUI + guarded Linux image-update pipeline.
# Windows: GUI on Windows, backend in WSL2 Ubuntu.
# macOS: run GUI inside an Ubuntu VM with shared folders.
# Linux: native Linux with sudo, loop devices, rsync and PiShrink.

import os
import platform
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk, simpledialog

APP_VERSION = "0.4.4"
APP_TITLE = "ONYX-Pro Image Builder"

WORKER = '#!/usr/bin/env bash\nset -Eeuo pipefail\nREPO="$1"; OLD_IMG="$2"; WORK_IMG="$3"; SHRUNK_IMG="$4"; ZIP_FILE="$5"; VERSION="$6"; MODE="$7"\nlog() { printf \'[ONYX] %s\\n\' "$*"; }\ndie() { printf \'[ERROR] %s\\n\' "$*" >&2; exit 1; }\n\nfor cmd in rsync losetup lsblk mount umount cp sha256sum zip awk tee; do\n  command -v "$cmd" >/dev/null 2>&1 || die "Falta el comando requerido: $cmd"\ndone\ncommand -v pishrink.sh >/dev/null 2>&1 || die "No se encuentra pishrink.sh en el entorno Linux."\n[[ -d "$REPO/Raspi" ]] || die "El repositorio seleccionado no contiene Raspi/: $REPO/Raspi"\n[[ -f "$OLD_IMG" ]] || die "No existe la imagen comercial antigua: $OLD_IMG"\n\nif [[ "$MODE" == "preview" ]]; then\n  log "PREVISUALIZACIÓN DETALLADA: la imagen se conectará SOLO EN LECTURA."\nelse\n  [[ ! -e "$WORK_IMG" && ! -e "$SHRUNK_IMG" && ! -e "$ZIP_FILE" ]] || die "Uno de los destinos ya existe. No se sobrescribirá."\nfi\n\nMOUNT_DIR="$(mktemp -d /tmp/onyx-builder.XXXXXX)"\nLOOPDEV=""; MOUNTED=0\ncleanup() {\n  set +e\n  sync\n  [[ "$MOUNTED" == "1" ]] && umount "$MOUNT_DIR"\n  [[ -n "$LOOPDEV" ]] && losetup -d "$LOOPDEV"\n  rmdir "$MOUNT_DIR" 2>/dev/null\n}\ntrap cleanup EXIT\n\nif [[ "$MODE" == "preview" ]]; then\n  IMAGE_TO_INSPECT="$OLD_IMG"\n  log "Conectando imagen comercial en modo de solo lectura..."\n  LOOPDEV="$(losetup --read-only --find --show --partscan "$IMAGE_TO_INSPECT")"\nelse\n  log "Copiando imagen comercial antigua a una imagen de trabajo independiente..."\n  cp --sparse=always --reflink=auto "$OLD_IMG" "$WORK_IMG"\n  sync\n  IMAGE_TO_INSPECT="$WORK_IMG"\n  log "Conectando copia de trabajo..."\n  LOOPDEV="$(losetup --find --show --partscan "$IMAGE_TO_INSPECT")"\nfi\n\nudevadm settle 2>/dev/null || true\nsleep 2\nROOT_PART=""\nwhile read -r name fstype label; do\n  if [[ "$fstype" == "ext4" || "$label" == "rootfs" ]]; then\n    ROOT_PART="$name"\n    [[ "$label" == "rootfs" ]] && break\n  fi\ndone < <(lsblk -nrpo NAME,FSTYPE,LABEL "$LOOPDEV")\n[[ -n "$ROOT_PART" ]] || die "No se encontró una partición ext4/rootfs."\n\nif [[ "$MODE" == "preview" ]]; then\n  mount -o ro,noload "$ROOT_PART" "$MOUNT_DIR"\nelse\n  mount "$ROOT_PART" "$MOUNT_DIR"\nfi\nMOUNTED=1\n\nIMAGE_REPO="$MOUNT_DIR/home/onyx/ONYX-Pro"\nTARGET_RASPI="$IMAGE_REPO/Raspi"\n[[ -d "$IMAGE_REPO" && -d "$TARGET_RASPI" ]] || die "No existe /home/onyx/ONYX-Pro/Raspi en la imagen."\n\n# Keep preview and execution rules identical.\nRSYNC_EXCLUDES=(\n  --exclude=\'/.micropico\'\n  --exclude=\'/CHANGELOG*\'\n  --exclude=\'/.git/\'\n  --exclude=\'/__pycache__/\'\n  --exclude=\'*.pyc\'\n  --exclude=\'/.lgd-nfy0\'\n  --exclude=\'/run_with_log.sh\'\n)\n\nif [[ "$MODE" == "preview" ]]; then\n  log "Origen: $REPO/Raspi/"\n  log "Destino: imagen comercial:/home/onyx/ONYX-Pro/Raspi/"\n  log "Reglas: CHANGELOG, run_with_log.sh, .git, __pycache__, .pyc y .lgd-nfy0 excluidos."\n  log "Comparando archivos con rsync --dry-run; no se copiará ni eliminará nada..."\n  REPORT_FILE="$(mktemp /tmp/onyx-rsync-preview.XXXXXX)"\n  rsync -ani --delete --itemize-changes --out-format=\'%i %n%L\' \\\n    "${RSYNC_EXCLUDES[@]}" --no-owner --no-group --no-perms --no-times \\\n    "$REPO/Raspi/" "$TARGET_RASPI/" | tee "$REPORT_FILE"\n  ADDED="$(awk \'$1 ~ /^>f/ && index($1, "+++++++++") > 0 {n++} END {print n+0}\' "$REPORT_FILE")"\n  UPDATED="$(awk \'$1 ~ /^>f/ && index($1, "+++++++++") == 0 {n++} END {print n+0}\' "$REPORT_FILE")"\n  DELETED="$(awk \'$1 ~ /^\\*deleting/ {n++} END {print n+0}\' "$REPORT_FILE")"\n  rm -f "$REPORT_FILE"\n  log "RESUMEN DE CAMBIOS: nuevos=$ADDED | actualizados=$UPDATED | eliminados=$DELETED"\n  if [[ -f "$TARGET_RASPI/.micropico" ]]; then\n    log "ELIMINACIÓN PREVISTA: .micropico (archivo de configuración de desarrollo no utilizado)."\n  fi\n  if [[ -d "$IMAGE_REPO/Zero" ]]; then\n    log "NOTA: Zero existe en la imagen y se eliminaría de la COPIA durante el proceso completo."\n  else\n    log "NOTA: Zero no existe en la imagen comercial."\n  fi\n  log "PREVISUALIZACIÓN FINALIZADA. La imagen original no fue modificada."\n  exit 0\nfi\n\nlog "Sincronizando exclusivamente Raspi (sin copiar permisos/fechas de Windows)..."\nlog "Archivos de desarrollo/documentación excluidos."\nrsync -a --delete --itemize-changes "${RSYNC_EXCLUDES[@]}" --no-owner --no-group --no-perms --no-times "$REPO/Raspi/" "$TARGET_RASPI/"\nif [[ -e "$TARGET_RASPI/.micropico" ]]; then\n  log "Eliminando .micropico de la copia comercial (archivo de desarrollo no utilizado)..."\n  rm -f -- "$TARGET_RASPI/.micropico"\nfi\n\nif [[ -d "$IMAGE_REPO/Zero" ]]; then\n  log "Eliminando Zero de la copia comercial (regla confirmada)..."\n  rm -rf -- "$IMAGE_REPO/Zero"\nfi\n\nONYX_UID="$(stat -c \'%u\' "$MOUNT_DIR/home/onyx")"\nONYX_GID="$(stat -c \'%g\' "$MOUNT_DIR/home/onyx")"\nchown -R "$ONYX_UID:$ONYX_GID" "$TARGET_RASPI"\n\nlog "Validando archivos esenciales..."\nfor f in main.py controller.py game.py robot.py sensors.py config.py; do\n  [[ -f "$TARGET_RASPI/$f" ]] || die "Falta Raspi/$f."\ndone\nSERVICE="$MOUNT_DIR/etc/systemd/system/onyx.service"\n[[ -f "$SERVICE" ]] || die "No se encuentra onyx.service."\ngrep -q \'WorkingDirectory=/home/onyx/ONYX-Pro/Raspi\' "$SERVICE" || die "WorkingDirectory de onyx.service no coincide."\ngrep -q \'main.py\' "$SERVICE" || die "ExecStart no apunta a main.py."\n[[ -L "$MOUNT_DIR/etc/systemd/system/multi-user.target.wants/onyx.service" ]] || die "onyx.service no parece habilitado."\n[[ ! -d "$IMAGE_REPO/Zero" ]] || die "La carpeta Zero sigue presente."\nlog "Propietario Raspi: $(stat -c \'%u:%g\' "$TARGET_RASPI")"\nsync\numount "$MOUNT_DIR"; MOUNTED=0\nlosetup -d "$LOOPDEV"; LOOPDEV=""\nrmdir "$MOUNT_DIR"; trap - EXIT\n\nlog "Ejecutando PiShrink con expansión automática habilitada (sin opción -s)..."\npishrink.sh "$WORK_IMG" "$SHRUNK_IMG"\n[[ -s "$SHRUNK_IMG" ]] || die "PiShrink no generó la imagen reducida."\n\nlog "Creando ZIP..."\n(cd "$(dirname "$ZIP_FILE")" && zip -q -j "$ZIP_FILE" "$SHRUNK_IMG")\nlog "Generando SHA-256..."\nsha256sum "$SHRUNK_IMG" "$ZIP_FILE" > "${ZIP_FILE}.sha256"\nlog "Proceso finalizado."\nlog "Imagen de trabajo: $WORK_IMG"\nlog "Imagen reducida: $SHRUNK_IMG"\nlog "ZIP: $ZIP_FILE"\nlog "Hashes: ${ZIP_FILE}.sha256"\n'

def detect_platform():
    if sys.platform.startswith("win"):
        return "Windows", "WSL2 Ubuntu"
    if sys.platform == "darwin":
        return "macOS", "Ubuntu VM requerida"
    return platform.system(), "Linux nativo"

class App:
    def __init__(self, root):
        self.root = root
        self.os_name, self.backend = detect_platform()
        self.repo = tk.StringVar()
        self.old_img = tk.StringVar()
        self.out_dir = tk.StringVar()
        self.version = tk.StringVar(value="1.1.0")
        self.status = tk.StringVar(value="Seleccioná las rutas para comenzar")
        self.root.title(f"{APP_TITLE} | v{APP_VERSION}")
        self.root.geometry("900x760")
        self.root.minsize(680, 560)
        self.root.configure(bg="#11151c")
        self.style()
        self.ui()

    def style(self):
        s = ttk.Style()
        try: s.theme_use("clam")
        except tk.TclError: pass
        s.configure("TEntry", fieldbackground="#202833", foreground="#edf2f7", insertcolor="#ffffff", padding=5)
        s.configure("TButton", font=("Segoe UI", 9), padding=(9, 5))
        s.configure("Accent.TButton", background="#1677d2", foreground="#ffffff", font=("Segoe UI", 9, "bold"), padding=(11, 6))
        s.map("Accent.TButton", background=[("active", "#238be8")])

    def ui(self):
        shell = tk.Frame(self.root, bg="#11151c"); shell.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(shell, bg="#11151c", highlightthickness=0)
        sb = ttk.Scrollbar(shell, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); self.canvas.pack(side="left", fill="both", expand=True)
        self.page = tk.Frame(self.canvas, bg="#11151c", padx=22, pady=16)
        self.win = self.canvas.create_window((0, 0), window=self.page, anchor="nw")
        self.page.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.win, width=e.width))
        self.canvas.bind_all("<MouseWheel>", self.wheel)
        self.build()

    def wheel(self, e):
        delta = int(e.delta / 120) if sys.platform != "darwin" else int(e.delta)
        self.canvas.yview_scroll(-delta, "units")

    def card(self, title, desc):
        f = tk.Frame(self.page, bg="#1a222d", padx=14, pady=11, highlightbackground="#2b3949", highlightthickness=1)
        tk.Label(f, text=title, bg="#1a222d", fg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(f, text=desc, bg="#1a222d", fg="#aab8c7", font=("Segoe UI", 8), wraplength=800, justify="left").pack(anchor="w", pady=(3, 8))
        f.pack(fill="x", pady=(0, 10)); return f

    def pathrow(self, parent, label, var, command, hint=""):
        row = tk.Frame(parent, bg="#1a222d"); row.pack(fill="x", pady=3)
        tk.Label(row, text=label, width=25, anchor="w", bg="#1a222d", fg="#e2eaf2", font=("Segoe UI", 8, "bold")).pack(side="left")
        ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(row, text="Examinar…", command=command).pack(side="right")
        if hint: tk.Label(parent, text=hint, bg="#1a222d", fg="#8798aa", font=("Segoe UI", 7)).pack(anchor="w")

    def build(self):
        p = self.page
        tk.Label(p, text="ONYX-Pro", bg="#11151c", fg="#63b3ff", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(p, text="Image Builder", bg="#11151c", fg="white", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(p, text=f"v{APP_VERSION} | {self.os_name} | Motor: {self.backend}", bg="#11151c", fg="#9aa8b8", font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 12))

        c = self.card("01 · Origen de desarrollo", "Seleccioná la carpeta raíz del repositorio ONYX-Pro. Solo se utilizará Raspi. Zero no se lee ni se compara.")
        self.pathrow(c, "Repositorio ONYX-Pro", self.repo, lambda: self.pick_dir(self.repo), "Debe contener Raspi/ (por ejemplo .../ONYX-Pro/Raspi).")
        c = self.card("02 · Imagen comercial antigua", "Se copiará a un archivo nuevo. El original no se modifica.")
        self.pathrow(c, "Imagen comercial (.img)", self.old_img, lambda: self.pick_file(self.old_img))
        c = self.card("03 · Destino", "Elegí una carpeta con espacio libre suficiente para una copia completa, la imagen reducida y el ZIP.")
        self.pathrow(c, "Carpeta de salida", self.out_dir, lambda: self.pick_dir(self.out_dir))
        row = tk.Frame(c, bg="#1a222d"); row.pack(fill="x", pady=4)
        tk.Label(row, text="Versión", bg="#1a222d", fg="#e2eaf2", font=("Segoe UI", 8, "bold")).pack(side="left")
        ttk.Entry(row, textvariable=self.version, width=16).pack(side="left", padx=8)

        c = self.card("04 · Reglas automáticas", "La previsualización monta la imagen antigua en solo lectura y compara Raspi sin modificarla. El proceso completo sincroniza Raspi y elimina archivos obsoletos, aplicando las exclusiones configuradas. Zero se elimina de la copia comercial.")
        tk.Label(c, text="✓ Solo Raspi del repositorio\n✓ Comparación previa sin modificar la imagen\n✓ Sincronización espejo de Raspi\n✓ Eliminar Zero de la copia\n✓ Validar archivos esenciales y onyx.service\n✓ PiShrink + ZIP + SHA-256", bg="#1a222d", fg="#c2d0de", justify="left", font=("Segoe UI", 8)).pack(anchor="w")
        tk.Label(p, text="IMPORTANTE: revisá el registro. El proceso completo modifica únicamente la copia de trabajo, nunca la imagen comercial original.", bg="#11151c", fg="#f0c477", font=("Segoe UI", 8), wraplength=820, justify="left").pack(anchor="w", pady=(0, 10))

        actions = tk.Frame(p, bg="#11151c"); actions.pack(fill="x")
        ttk.Button(actions, text="Previsualizar cambios (solo lectura)", style="Accent.TButton", command=self.preview).pack(side="left")
        ttk.Button(actions, text="Ejecutar proceso completo", command=self.run_full).pack(side="left", padx=7)
        ttk.Button(actions, text="Limpiar", command=self.clear).pack(side="left")
        self.progress = ttk.Progressbar(p, mode="indeterminate"); self.progress.pack(fill="x", pady=(12, 5))
        tk.Label(p, textvariable=self.status, bg="#11151c", fg="#9aa8b8", font=("Segoe UI", 8)).pack(anchor="w")
        self.log = tk.Text(p, height=12, bg="#0b1016", fg="#c9d5e2", insertbackground="white", font=("Consolas", 8), relief="flat", wrap="word")
        self.log.pack(fill="both", expand=True, pady=(8, 0))
        self.log.insert("end", "Los mensajes y resultados aparecerán aquí.\n"); self.log.configure(state="disabled")

    def pick_dir(self, var):
        x = filedialog.askdirectory()
        if x: var.set(x)

    def pick_file(self, var):
        x = filedialog.askopenfilename(filetypes=[("Imagen de disco", "*.img"), ("Todos", "*.*")])
        if x: var.set(x)

    def log_line(self, line):
        self.log.configure(state="normal"); self.log.insert("end", line + "\n"); self.log.see("end"); self.log.configure(state="disabled")

    def validate(self):
        repo = Path(self.repo.get()).expanduser() if self.repo.get().strip() else None
        old = Path(self.old_img.get()).expanduser() if self.old_img.get().strip() else None
        out = Path(self.out_dir.get()).expanduser() if self.out_dir.get().strip() else None
        version = self.version.get().strip()
        errors = []
        if repo is None or not (repo / "Raspi").is_dir(): errors.append("El repositorio debe contener Raspi/.")
        if old is None or not old.is_file(): errors.append("Seleccioná una imagen comercial .img existente.")
        if out is None or not out.is_dir(): errors.append("Seleccioná una carpeta de salida existente.")
        if not version or any(ch not in "0123456789.-" for ch in version): errors.append("Versión inválida. Ejemplo: 1.1.0.")
        if errors:
            messagebox.showerror("Revisá los datos", "\n\n".join(errors)); return None
        stem = f"ONYX-Pro_Commercial_v{version}"
        work, shrunk, zipf = out / f"{stem}_Working.img", out / f"{stem}_Shrunk.img", out / f"{stem}.zip"
        for f in (work, shrunk, zipf, Path(str(zipf) + ".sha256")):
            if f.exists():
                messagebox.showerror("Destino existente", f"Ya existe:\n{f}\n\nElegí otra carpeta o retiralo manualmente."); return None
        return repo.resolve(), old.resolve(), work, shrunk, zipf, version

    def backend_command(self, vals, mode):
        repo, old, work, shrunk, zipf, version = vals
        if sys.platform.startswith("win"):
            wsl = shutil.which("wsl.exe") or shutil.which("wsl")
            if not wsl: raise RuntimeError("No se encontró wsl.exe. Instalá WSL2 con Ubuntu.")
            def wp(path):
                # Normalize Windows backslashes before passing the argument to WSL.
                # PowerShell/WSL may otherwise strip separators in paths such as C:\\Users\\...
                win_path = str(path).replace("\\", "/")
                r = subprocess.run(
                    [wsl, "-d", "Ubuntu-24.04", "--", "wslpath", "-a", win_path],
                    capture_output=True, text=True, encoding="utf-8", errors="replace"
                )
                if r.returncode:
                    detail = (r.stderr or r.stdout).strip()
                    raise RuntimeError(
                        "No se pudo convertir la ruta a WSL: " + str(path) +
                        (("\\n" + detail) if detail else "")
                    )
                converted = r.stdout.strip()
                if not converted.startswith("/"):
                    raise RuntimeError(
                        "WSL devolvió una ruta no válida para: " + str(path) +
                        "\\nResultado: " + converted
                    )
                return converted
            paths = [wp(repo), wp(old), wp(work), wp(shrunk), wp(zipf)]
            quoted = " ".join("'" + x.replace("'", "'\\''") + "'" for x in paths + [version, mode])
            # Both modes mount a disk image. Preview mounts it read-only, but still needs sudo.
            return [wsl, "-d", "Ubuntu-24.04", "--", "/bin/bash", "-lc",
                    "sudo -S -p '' /bin/bash -s -- " + quoted]

        if sys.platform == "darwin":
            raise RuntimeError("En macOS, ejecutá esta aplicación dentro de una VM Ubuntu con la carpeta compartida montada. macOS no monta ext4 de forma nativa.")
        args = ["/bin/bash", "-s", "--", str(repo), str(old), str(work), str(shrunk), str(zipf), version, mode]
        return ["sudo", "-S", "-p", "", *args]

    def execute(self, mode):
        vals = self.validate()
        if not vals: return
        if mode == "full":
            msg = ("Se creará una copia de la imagen antigua y se actualizará SOLO Raspi.\\n"
                   "Se eliminará Zero de la copia si existe. Los archivos ausentes en el repositorio Raspi "
                   "se eliminarán del destino según las exclusiones configuradas.\\n\\n"
                   "Después se validará onyx.service y se ejecutará PiShrink, ZIP y SHA-256.\\n\\n¿Continuar?")
        else:
            msg = "Se montará la imagen comercial antigua SOLO EN LECTURA y se comparará Raspi con rsync --dry-run. No se copiará ni eliminará ningún archivo. Ubuntu solicitará la contraseña para montar la imagen.\\n\\n¿Continuar?"
        if not messagebox.askyesno("Confirmar", msg): return

        password = None
        password = simpledialog.askstring(
            "Permisos de Ubuntu",
            ("Para inspeccionar la imagen, Ubuntu necesita permisos de administrador. "
             "En esta previsualización la imagen se monta SOLO EN LECTURA."
             if mode == "preview" else
             "Para modificar la copia de trabajo, Ubuntu necesita permisos de administrador.")
            + "\\n\\nIntroducí tu contraseña de Ubuntu (no la de Windows):",
            show="*",
            parent=self.root
        )
        if password is None: return
        if not password:
            messagebox.showwarning("Contraseña requerida", "No ingresaste la contraseña de Ubuntu.")
            return

        try: command = self.backend_command(vals, "sync" if mode == "full" else "preview")
        except Exception as e:
            messagebox.showerror("Backend no disponible", str(e)); return
        self.progress.start(10); self.status.set("Ejecutando en el entorno Linux…")
        self.log_line(f"--- {mode.upper()} ---")
        threading.Thread(target=self.worker, args=(command, password), daemon=True).start()

    def worker(self, command, password=None):
        try:
            # Binary pipes prevent Windows text mode from translating LF to CRLF.
            # Bash would otherwise parse "pipefail\\r" as an invalid option.
            proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=False, bufsize=0)
            assert proc.stdin and proc.stdout
            if password is not None:
                proc.stdin.write(password.encode("utf-8") + b"\n")
            proc.stdin.write(WORKER.encode("utf-8"))
            proc.stdin.close()
            for raw_line in proc.stdout:
                line = raw_line.decode("utf-8", errors="replace")
                self.root.after(0, self.log_line, line.rstrip())
            code = proc.wait()
            self.root.after(0, self.finish, code)
        except Exception as e:
            self.root.after(0, self.finish_error, str(e))

    def finish(self, code):
        self.progress.stop()
        if code == 0:
            self.status.set("Proceso terminado correctamente")
            messagebox.showinfo(APP_TITLE, "La operación terminó correctamente. Revisá el registro.")
        else:
            self.status.set(f"Error del backend: código {code}")
            messagebox.showerror(APP_TITLE, f"El proceso terminó con código {code}. Revisá el registro.")

    def finish_error(self, error):
        self.progress.stop(); self.status.set("Error al ejecutar")
        self.log_line("[ERROR] " + error); messagebox.showerror(APP_TITLE, error)

    def preview(self): self.execute("preview")
    def run_full(self):
        if sys.platform == "darwin":
            messagebox.showinfo("macOS", "Ejecutá esta aplicación dentro de una VM Ubuntu. Luego podremos habilitar el backend Linux.")
            return
        self.execute("full")

    def clear(self):
        self.repo.set(""); self.old_img.set(""); self.out_dir.set(""); self.status.set("Selección limpiada")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
