#!/bin/bash
# Setup virtuálního prostředí na macOS/Linux
# Spusťte: bash scripts/setup.sh

echo "Setup Python prostředí - Finance"
echo "================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Ověř Python
echo ""
echo "Kontrola Python..."
if ! command -v python3 &> /dev/null; then
    echo "Chyba: Python3 není nainstalován"
    echo "Na macOS: brew install python3"
    echo "Na Ubuntu/Debian: sudo apt-get install python3 python3-venv python3-pip"
    exit 1
fi

python_version=$(python3 --version)
echo "Nalezen: $python_version"

# Vytvoř virtuální prostředí
VENV_PATH="$ROOT_DIR/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo ""
    echo "Vytváření virtuálního prostředí..."
    python3 -m venv "$VENV_PATH"
    if [ $? -ne 0 ]; then
        echo "Chyba při vytváření virtuálního prostředí"
        exit 1
    fi
    echo "Virtuální prostředí vytvořeno: $VENV_PATH"
else
    echo ""
    echo "Virtuální prostředí již existuje"
fi

# Aktivuj virtuální prostředí
echo ""
echo "Aktivace virtuálního prostředí..."
source "$VENV_PATH/bin/activate"

# Upgraduj pip
echo ""
echo "Upgrade pip..."
python -m pip install --upgrade pip --quiet

# Instaluj závislosti
REQUIREMENTS_PATH="$ROOT_DIR/requirements.txt"
if [ -f "$REQUIREMENTS_PATH" ]; then
    echo ""
    echo "Instalace závislostí z requirements.txt..."
    pip install -r "$REQUIREMENTS_PATH" --quiet
    if [ $? -eq 0 ]; then
        echo "Všechny závislosti nainstalovány"
    else
        echo "Chyba při instalaci závislostí"
        exit 1
    fi
else
    echo "Soubor requirements.txt nenalezen"
fi

echo ""
echo "================================="
echo "Setup dokončen!"
echo "================================="
echo ""
echo "Aktivace prostředí:"
echo "source scripts/activate.sh"
echo ""
echo "Spuštění skriptu:"
echo "python src/qqq_gap_analysis.py"
