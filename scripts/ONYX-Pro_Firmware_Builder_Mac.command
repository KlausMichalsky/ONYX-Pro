#!/bin/bash
# ONYX-Pro Firmware Builder launcher for macOS
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="$(command -v python3)"
if [ -z "$PYTHON_BIN" ]; then
    echo "Python 3 was not found. Please install Python 3."
    read -r -p "Press Enter to close..."
    exit 1
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/ONYX-Pro_Firmware_Builder_v0.1.5.py"
