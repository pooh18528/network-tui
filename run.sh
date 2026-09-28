#!/usr/bin/env sh
# Network-TUI Launcher for macOS / Linux / BSD
# วิธีใช้:  chmod +x run.sh  (ครั้งเดียว)  แล้ว  ./run.sh
#        หรือ  sh run.sh

cd "$(dirname "$0")" || exit 1

echo "[ Network-TUI ] checking dependencies..."
if ! python3 -c "import textual, rich, psutil" >/dev/null 2>&1; then
    echo "installing dependencies..."
    python3 -m pip install -r requirements.txt || {
        echo "install failed — try: python3 -m pip install --upgrade pip"
        exit 1
    }
fi

echo ""
echo "Starting Network-TUI..."
echo "Q quit | R rescan | ? help (use a UTF-8 terminal, e.g. Terminal.app, GNOME Terminal, xterm)"
echo ""

exec python3 main.py "$@"
