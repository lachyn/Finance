#!/bin/bash
# Aktivace virtuálního prostředí na macOS/Linux
# Spusťte: source scripts/activate.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$ROOT_DIR/.venv"

if [ ! -d "$VENV_PATH" ]; then
    echo "Chyba: Virtuální prostředí neexistuje!"
    echo "Nejdřív spusťte: bash scripts/setup.sh"
    exit 1
fi

echo "Aktivace virtuálního prostředí..."
source "$VENV_PATH/bin/activate"
echo "Prostředí aktivováno!"
