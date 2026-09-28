# 🌐 Network-TUI

> English | [ไทย](README.th.md)

**Network scanner with TUI — see users • devices • models on your LAN**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

> Scan your Wi-Fi / LAN and show every device in a live table —
> **IP, MAC, Vendor, Hostname, Model, Device type**

---

## ✨ Features

| Feature | Details |
|---------|-------------|
| 🔍 **Network scan** | Ping sweep over the subnet (e.g. 192.168.1.0/00) + ARP table |
| 🏷️ **Vendor** | From OUI (first 6 MAC chars) — 300+ vendors (Apple, Samsung, Xiaomi, TP-Link, Huawei, …) |
| 💻 **Hostname** | Reverse DNS + NetBIOS (`nbtstat -A`) |
| 📱 **Model** | Guessed from Hostname + Vendor (iPhone, Galaxy, Redmi, POCO, ThinkPad, ESP32, Printer, TV, Console …) |
| 🏷️ **Device type** | 📱 Phone 💻 Laptop 🖥️ PC 🌐 Router 📺 TV 🖨️ Printer 🎮 Console 💡 IoT 🔊 Smart Speaker |
| 🌐 **Gateway & Self** | Highlights Router/Gateway (🌐GW) and your own machine (⭐YOU) |
| ⚡ **TUI** | Built with [Textual](https://textual.textualize.io/) — hotkeys, filter, sort, Export |
| 📊 **Header info** | Interface, Local IP, CIDR, Gateway, MAC, online device count |
| 💾 **Export CSV** | Press `E` to save `network_scan_YYYYMMDD_HHMMSS.csv` (UTF-8 BOM, opens in Excel) |
| 🔄 **Multi-Interface** | Multiple networks (Wi-Fi + Ethernet + WSL + VMnet)? Press `I` to switch |

---

## 📸 TUI preview

![Main screen — device table + detail pane](img/tui-main.png)

![Command palette — Ctrl+P, includes Switch language](img/palette.png)

```
┌─ 🌐 Network-TUI ────────────────────────────── 22:58:32 ─┐
│ MY-PC 192.168.1.--- · 192.168.1.0/-- · GW 192.168.1.-     │
│ Wi-Fi · 📊 7/9 · 🔒 5 · ✏️ 2/9 #1 ✓ Ready                 │
├──────────────────────────────┬────────────────────────────┤
│ #  IP             Vendor… Model… Status │ 🔍 192.168.1.---           │
│ 1  192.168.1.- 🌐  Fiber… Router… 🟢 on │ MAC  ----------------     │
│ 5  192.168.1.---⭐ Unkno… Windo… 🟢 on │ Model Xiaomi Phone…        │
│ ... (←/→ scroll · ↑/↓ select → details)│ 💡 N rename this device    │
└──────────────────────────────┴────────────────────────────┘
 R Scan · F Filter · S Sort · ⇧S Reverse · E Export · I Switch net · N Rename · L Lang · Q Quit · ? Help
```
> Wide screen → compact table + **detail pane on the right** (↑↓ to see full info, no `…` truncation)
> Medium screen → table stretches full width · Narrow screen → unimportant columns auto-hide (`MAC` → `Type` → `Ping` …), see the rest with `←/→`

---

## 🚀 Install & Run

Supports **Windows / macOS / Linux / OpenBSD** — per-OS capabilities in the table below.

### Option 1 — Install as `network-tui` command (recommended, works anywhere)

```bash
# once, from the project folder
cd Network-tui
pip install .
# Windows, first time: close and reopen the terminal (PATH refresh)

# then callable from any folder
network-tui              # open TUI
network-tui --cli        # CLI scan
network-tui --version    # check version
network-tui --help       # all options
```

> Upgrade: `pip install --upgrade .` (in project folder) · Uninstall: `pip uninstall network-tui`

### Option 2 — Run directly, no install

```bash
cd Network-tui
pip install -r requirements.txt
python main.py            # open TUI (same as network-tui)
python main.py --cli      # CLI mode
```

> ⚠️ On Windows use **Windows Terminal** (not legacy cmd), otherwise Thai/emoji renders garbled.

### 📖 First run (read this first — for friends who just downloaded it)

**Step 0 — 2 prerequisites**

1. Install **Python 3.10+** and verify:
   ```bash
   python --version     # must show Python 3.10.x or newer
   ```
   - Windows: download from python.org (tick `Add python.exe to PATH` during install)
   - macOS: `brew install python` · Linux: `sudo apt install python3-pip` · OpenBSD: `doas pkg_add python3 py3-pip py3-psutil`
2. Get the code: `git clone <repo-url>` then `cd Network-tui` (or download ZIP from GitHub → extract → enter folder)

**Step 1 — Pick one way to run (identical results)**

| If you | Use | Command |
|---|---|---|
| Want it long-term, short commands | A: install once | `pip install .` then `network-tui` from anywhere |
| Just want a quick try | B: no install | `pip install -r requirements.txt` then `python main.py` |

Verify: `network-tui --version` (option A) must show `network-tui 2.5.0`

**Step 2 — What the first launch looks like**

1. Type `network-tui` (or `python main.py`) → table stays empty briefly: **first scan takes ~30–60 seconds**, wait for it
2. The first scan saves devices as baseline (shows `📌 ...baseline...`) — next time a rogue device appears you'll get a `🆕` alert automatically
3. 5 keys are enough: `R` rescan · `N` rename selected · `L` switch TH/EN · `E` save CSV · `Q` quit (press `?` for the rest)

**Step 3 — Name your own phone (once, remembered forever)**

1. Find your machine in the MAC column
2. Copy the example file: `aliases.example.json` → `aliases.json` (Windows: copy-paste and rename)
3. Edit MAC + name/model, press `R` to rescan — the name sticks forever

**Step 4 — Common issues**

| Symptom | Fix |
|---|---|
| `network-tui: command not found` | Close and reopen the terminal (PATH not refreshed) or `pip install .` again |
| Garbled/boxed text | Switch to Windows Terminal (Windows) / a UTF-8 terminal |
| Only gateway + self (2 devices) | That network uses Client Isolation (dorm/campus) — not a bug, see 🏫 |
| Slow/stuck scan | Let the first round finish, or use `network-tui --cli --timeout 400 --workers 100` |
| Dorm/campus network | Read 🏫 + ⚖️ first — only scan authorized networks |

### Per-OS notes (applies to option 1 on every OS)

- **Windows**: plain `pip install .`; if `network-tui` not found, reopen the terminal (PATH) or double-click `run.bat`
- **macOS**: needs python 3.10+ (`brew install python`) · if `ping localhost` fails, turn off Stealth Mode: System Settings → Network → Firewall → Options
- **Linux**: Debian/Ubuntu `sudo apt install python3-pip` · Fedora `sudo dnf install python3-pip` (rest is the same `pip install .`)
- **OpenBSD**: `doas pkg_add python3 py3-pip py3-psutil` first, then `python3 -m pip install .`

### Per-OS capabilities

| Feature | Windows | macOS | Linux | OpenBSD |
|---|---|---|---|---|
| Ping + ARP scan | ✅ | ✅ | ✅ | ✅ |
| Auto gateway | ✅ | ✅ | ✅ | ✅ (best-effort) |
| Hostname (reverse DNS) | ✅ | ✅ | ✅ | ✅ |
| NetBIOS (`nbtstat`) | ✅ Windows only | — | — | — |
| TUI / CLI / Export | ✅ | ✅ | ✅ | ✅ |

### Option 2 — CLI (no TUI)

```powershell
# scan and print table to console
python main.py --cli

# scan and auto-export CSV/JSON (by extension)
python main.py --cli --export auto
python main.py --cli --export result.json

# choose interface
python main.py --cli -i "Wi-Fi"

# tune speed (timeout 200-5000ms, workers 10-200)
python main.py --cli --timeout 400 --workers 100

# list all interfaces
python main.py --list-interfaces

# all options
python main.py --help
```

---

## ⌨️ TUI hotkeys

| Key | Action |
|-----|--------|
| `R` / `F5` | 🔄 Rescan |
| `F` / `/` | 🔍 Filter (IP / MAC / vendor / hostname / model) |
| `S` | ↕️ Change sort (IP → vendor → hostname → type → latency) |
| `Shift+S` | ↕️ Reverse sort direction |
| `E` | 💾 Export CSV |
| `I` | 🔌 Switch interface (if multiple) |
| `N` / `Enter` | ✏️ Rename selected device (saved in `aliases.json`) |
| `L` | 🌐 Switch language ไทย ⇄ English (remembered next time) |
| `?` | ❓ Help |
| `Q` | 🚪 Quit |

### 🌐 Language (TH/EN)

- In TUI press `L` for instant Thai/English (headers, side pane, menus, guessed model names all switch — rescans once). Choice is saved in `settings.json`
- CLI: `python main.py --cli --lang th` for Thai (omit = saved value, default English)

---

## 🛡️ Security — rogue device alerts

Every scan remembers MACs in `known_devices.json` and diffs automatically:

| Event | What you see |
|---|---|
| First scan | 📌 Baseline saved (all devices) |
| New MAC | 🆕 badge in Status + alert (neighbor's phone / rogue device) |
| MAC gone > 24h | ⚠️ Alert (avoids flapping from one missed scan) |
| Same MAC, new IP | 🔁 Alert (usually DHCP move, but also an ARP-spoofing symptom) |

The right detail pane shows **first seen / last seen** for the selected machine.

> Note: `known_devices.json` / `aliases.json` contain your home MACs — already git-ignored, never push to a public repo · only scan your own networks

---

## 🏫 Campus / dorm / office Wi-Fi — does it work?

Yes, **on whatever network you're connected to**, with caveats:

| Network | Result |
|---|---|
| Dorm / home / small office (normal /24) | ✅ Full features like home |
| eduroam / campus Wi-Fi (often /16 + Client Isolation) | ⚠️ Gateway + self only — the AP blocks clients from seeing each other (not a bug) |
| Large networks (/16 = 65,536 IPs) | App scans only the **nearby /24 (254 IPs)** + ARP-known hosts, and tells you (pinging everything is slow and rude) |
| Captive portal (dorm/campus login page) | Log in first, then scan |

> ⚖️ **Important rule**: only scan authorized networks (your dorm / a lab your teacher approved). Many campuses ban scanning — you can get IDS-flagged / MAC-banned. Ask IT when unsure.

---

## 🔧 Want better accuracy?

1. **Run as Administrator** — fuller ARP + NetBIOS
   ```powershell
   # Right-click PowerShell → Run as Administrator → then python main.py
   ```

2. **Join the same Wi-Fi as your devices** — different bands/subnets (e.g. 2.4GHz vs 5GHz) won't see each other

3. **Firewall** — some devices ignore ping (e.g. locked iPhone); unlock the screen or turn off Private Wi-Fi Address

---

## 📁 Project structure

```
Network-tui/
├── main.py                 # entry point (calls network_tui.cli)
├── pyproject.toml          # install as `network-tui` command
├── requirements.txt
├── run.bat / run.sh
├── README.md / README.th.md
├── aliases.example.json    # device-name example (copy to aliases.json)
└── network_tui/
    ├── __init__.py
    ├── app.py              # Textual TUI
    ├── cli.py              # CLI + entry point
    ├── scanner.py          # scan (ping sweep + ARP + hostname)
    ├── history.py          # remembers devices + new/gone alerts
    ├── oui.py              # Vendor DB + model guess
    ├── lang.py             # TH/EN
    ├── models.py           # Device / NetworkInfo dataclass
    └── utils.py            # helpers (ping, ip, hostname)
```

---

## 🧠 How model guessing works?

`oui.py` in 2 steps:

1. **Vendor** — OUI (first 6 MAC chars) against a 300+ entry DB
2. **Model** — hostname patterns + vendor:
   - `iphone`, `ipad`, `macbook` → Apple
   - `galaxy`, `SM-` → Samsung Galaxy
   - `redmi`, `poco`, `m210` → Xiaomi
   - `esp_`, `tasmota`, `shelly` → ESP/IoT
   - `playstation`, `xbox`, `switch` → Console
   - `brother`, `epson`, `canon` → Printer
   - …

Unknown ones show as `Vendor Device` or `Unknown Device`

---

## 🛠️ Troubleshooting

| Problem | Fix |
|-------|-----|
| **No devices at all** | Run `python main.py --cli` to check / verify Wi-Fi is connected / try `arp -a` in PowerShell for other IPs |
| **Only gateway + self** | Client Isolation network, or devices block ping — scan while devices are active (screen on) |
| **Hostname is `-`** | Some machines don't answer reverse DNS — rename the machine to include the model (e.g. `iPhone-Witcha`) |
| **Vendor Unknown** | Randomized MACs on newer phones — turn off Private Wi-Fi Address in Wi-Fi settings and reconnect |
| **Textual won't install** | `pip install --upgrade pip` first, then `pip install textual rich psutil` |
| **Slow scan** | Lower `--timeout` / raise `--workers`, e.g. `python main.py --cli --timeout 400 --workers 100` |

---

## 📜 License

MIT — free to use and modify

---

## 💡 Future ideas

- [ ] Port scan (80, 443, 22) for better model guesses
- [ ] mDNS / SSDP discovery (clearer printer/TV model names)
- [ ] Real-time traffic graph (psutil net_io)
- [ ] Dark/Light theme toggle
- [x] Scan history + join/leave diff (done — `history.py`)

> Want something added? Just ask! — built with Network-TUI 🌐
