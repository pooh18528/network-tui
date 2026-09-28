#!/usr/bin/env python3
"""Network-TUI — thin launcher (ติดตั้งแบบ pip แล้วใช้คำสั่ง `network-tui` ได้เลย).

Legacy entry kept working: `python main.py ...` == `network-tui ...`
"""
from network_tui.cli import main

if __name__ == "__main__":
    main()
