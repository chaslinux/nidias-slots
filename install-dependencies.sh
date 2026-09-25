#!/usr/bin/env bash

set -e

PROJECT_DIR="$HOME/Code/nidias-slots"
VENV_DIR="$PROJECT_DIR/.venv"

echo "Creating project directory..."
mkdir -p "$PROJECT_DIR"

echo "Installing system dependencies..."
sudo apt update

sudo apt install -y python3 python3-full python3-venv python3-pip python3-tk papirus-icon-theme librsvg2-bin oxygen-sounds ubuntu-sounds cairosvg python3-pygame

echo "Creating Python virtual environment..."

if [ -d "$VENV_DIR" ]; then
echo "Removing existing virtual environment..."
rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"

echo "Installing Python dependencies..."

"$VENV_DIR/bin/python" -m pip install --upgrade pip

"$VENV_DIR/bin/python" -m pip install Pillow cairosvg pygame

echo
echo "=========================================="
echo "Nidia's Slots dependencies installed."
echo "=========================================="
echo
echo "Project directory:"
echo " $PROJECT_DIR"
echo
echo "Virtual environment:"
echo " $VENV_DIR"
echo
echo "To run Nidia's Slots:"
echo
echo " cd $PROJECT_DIR"
echo " .venv/bin/python nidias-slots.py"
echo
echo "The installer does NOT activate the virtual environment."
echo
