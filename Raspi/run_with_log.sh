
#!/bin/bash

# Directorio de los registros
LOG_DIR="$HOME/ONYX-Pro/Raspi/logs"

# Cantidad máxima de registros
MAX_LOGS=10

# Crear carpeta si no existe
mkdir -p "$LOG_DIR"

# Eliminar los registros más antiguos si superamos el límite
find "$LOG_DIR" -maxdepth 1 -type f -name "ONYX-Pro_Log_*.txt" \
    -printf '%T@ %p\n' | sort -nr | tail -n +$((MAX_LOGS + 1)) |
    cut -d' ' -f2- | while IFS= read -r file; do
        rm -f -- "$file"
    done

# Nombre del nuevo registro
LOG_FILE="$LOG_DIR/ONYX-Pro_Log_$(date +%Y-%m-%d_%H-%M-%S).txt"

echo "Registro guardado en: $LOG_FILE"

# Ejecutar ONYX-Pro y guardar toda la salida
python -u -b main.py 2>&1 | tee "$LOG_FILE"
