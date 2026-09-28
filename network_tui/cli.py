#!/usr/bin/env python3
"""Network-TUI — command-line entry point (`network-tui` หลัง pip install).

วิธีใช้หลังติดตั้ง:
    network-tui              # เปิด TUI
    network-tui --cli        # สแกนแบบ CLI
    network-tui --help       # ดูตัวเลือกทั้งหมด
"""
import argparse
import sys
import os


def ensure_utf8():
    """บังคับ UTF-8 บน Windows (แก้ปัญหาภาษาไทย + emoji) — เรียกครั้งเดียวพอ"""
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


ensure_utf8()


def run_tui():
    try:
        from .app import NetworkTUI
    except ImportError as e:
        print("❌ ต้องติดตั้ง dependencies ก่อน / install dependencies first:")
        print("   pip install network-tui")
        print(f"   Error: {e}")
        sys.exit(1)

    app = NetworkTUI()
    app.run()


def resolve_lang(cli_lang):
    """ภาษา: --lang > settings.json > อังกฤษ (default)"""
    from .lang import load_lang, set_current
    if cli_lang in ("th", "en"):
        set_current(cli_lang)
        return cli_lang
    return load_lang()


def run_cli_scan(args, lang="en"):
    """โหมด CLI แบบไม่ใช้ TUI — สแกนแล้วพิมพ์ตารางออกมา (สำหรับ debug / ไม่มี textual)"""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from .scanner import get_network_infos, scan_network
    from .lang import t
    from .utils import mask_ip, mask_mac, mask_text
    mask = bool(getattr(args, "mask", False))

    # legacy_windows=False แก้ emoji บน Windows + กว้างพอสำหรับตาราง
    console = Console(legacy_windows=False, force_terminal=False, width=140)

    infos = get_network_infos()
    if not infos:
        console.print(f"[red]{t('cli_no_iface', lang)}[/]")
        sys.exit(1)

    # เลือก interface — เทียบแบบ exact ก่อน แล้วค่อย contains (กัน "Wi" ไปโดน "Wi-Fi" ผิดตัว)
    info = infos[0]
    if args.interface:
        want = args.interface.strip().lower()
        exact = [inf for inf in infos if inf.interface.lower() == want or inf.local_ip == args.interface.strip()]
        if exact:
            info = exact[0]
        else:
            for inf in infos:
                if want in inf.interface.lower():
                    info = inf
                    break

    console.print(Panel(
        f"[cyan]Interface:[/] {info.interface}\n"
        f"[green]IP:[/] {info.local_ip}  [yellow]CIDR:[/] {info.cidr}  [magenta]Gateway:[/] {info.gateway}\n"
        f"[dim]{t('cli_scanning', lang, cidr=info.cidr)}[/]",
        title=t("cli_panel_title", lang),
        border_style="blue"
    ))

    def progress(done, total, ip, ok):
        if done % 25 == 0 or done == total:
            console.print(f"  ⏳ {done}/{total}  {ip} {'✓' if ok else '·'}")

    devices = scan_network(info, timeout_ms=args.timeout, max_workers=args.workers, progress_cb=progress, lang=lang)

    # เทียบประวัติ rogue-device
    try:
        from .history import check as history_check
        sec_new, sec_gone, sec_changed, sec_baseline = history_check(devices)
    except Exception:
        sec_new, sec_gone, sec_changed, sec_baseline = [], [], [], False

    table = Table(title=t("cli_table_title", lang, n=len(devices), cidr=info.cidr), show_lines=True, header_style="bold cyan", expand=True)
    table.add_column(t("cli_col_no", lang), style="dim", width=3, no_wrap=True)
    table.add_column("IP", style="cyan", no_wrap=True, min_width=14)
    table.add_column("MAC", style="dim", no_wrap=True, min_width=17)
    table.add_column(t("cli_col_vendor", lang), style="yellow", min_width=12, overflow="fold")
    table.add_column(t("cli_col_hostname", lang), style="white", min_width=12, overflow="fold")
    table.add_column(t("cli_col_model", lang), style="green", min_width=16, overflow="fold")
    table.add_column(t("cli_col_type", lang), style="magenta", min_width=10, no_wrap=True)
    table.add_column(t("cli_col_status", lang), style="green", min_width=14, overflow="fold")
    table.add_column("Latency (TTL)", style="yellow", justify="right", min_width=14, no_wrap=True)

    for idx, d in enumerate(devices, 1):
        status = d.status_label()
        latency = d.latency_label()
        ip_show = mask_ip(d.ip) if mask else d.ip
        mac_disp = (mask_mac(d.mac) if mask else d.mac) or "-"
        if d.is_randomized:
            mac_disp += " 🔒"
        vendor_disp = d.vendor
        if d.is_randomized and "Private" not in vendor_disp:
            vendor_disp = f"🔒 {vendor_disp}"
        host_show = (mask_text(d.hostname) if mask else d.hostname) or "-"
        table.add_row(
            str(idx),
            ip_show,
            mac_disp,
            vendor_disp,
            host_show,
            d.model,
            d.device_type,
            status,
            latency,
        )

    console.print(table)

    # หมายเหตุสภาพเครือข่าย: วงใหญ่ / Client Isolation
    try:
        if getattr(info, "scanned_cidr", "") and getattr(info, "total_hosts", 0) > 512:
            console.print(f"[cyan]{t('net_big', lang, orig=info.cidr, n=info.total_hosts, cidr=info.scanned_cidr)}[/]")
        online_n = sum(1 for d in devices if d.status == "online")
        if devices and online_n <= 2:
            console.print(f"[yellow]{t('net_isolation', lang, n=online_n)}[/]")
    except Exception:
        pass

    # สรุป security: baseline / ใหม่ / หาย / IP เปลี่ยน
    if sec_baseline and devices:
        console.print(f"\n[cyan]{t('sec_baseline', lang, n=len(devices))}[/]")
    else:
        if sec_new:
            ips = ", ".join(d.ip for d in sec_new[:5]) + ("…" if len(sec_new) > 5 else "")
            console.print(f"\n[yellow]{t('sec_new', lang, n=len(sec_new), ips=ips)}[/]")
        if sec_gone:
            ips = ", ".join(g.get("ip", "?") for g in sec_gone[:5]) + ("…" if len(sec_gone) > 5 else "")
            console.print(f"[red]{t('sec_gone', lang, n=len(sec_gone), ips=ips)}[/]")
        if sec_changed:
            pairs = ", ".join(f"{c['device'].ip} ({c['old_ip']}->{c['new_ip']})" for c in sec_changed[:5])
            console.print(f"[yellow]{t('sec_changed', lang, n=len(sec_changed), pairs=pairs)}[/]")

    # แจ้ง Private MAC
    private_count = sum(1 for d in devices if getattr(d, 'is_randomized', False))
    if private_count:
        console.print(f"\n[yellow]{t('cli_private1', lang, n=private_count)}[/]")
        console.print(f"[dim]{t('cli_private2', lang)}[/]")
        console.print(f"[dim]{t('cli_private3', lang)}[/]")

    if args.export:
        import csv
        import json
        from datetime import datetime
        from pathlib import Path
        filename = args.export if args.export != "auto" else f"network_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        out_path = Path(filename)
        if out_path.parent.as_posix() not in ("", "."):
            out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.suffix.lower() == ".json":
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump([d.to_dict() for d in devices], f, ensure_ascii=False, indent=2)
        else:
            with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["#", "IP", "MAC", "Vendor", "Hostname", "Model", "Type", "Status", "Latency", "TTL", "Randomized"])
                for idx, d in enumerate(devices, 1):
                    w.writerow([idx, d.ip, d.mac, d.vendor, d.hostname, d.model, d.device_type, d.status, d.latency_ms or "", getattr(d, 'ttl', '') or "", "YES" if getattr(d, 'is_randomized', False) else ""])
        console.print(f"[green]{t('cli_exported', lang, f=out_path)}[/]")

    console.print(f"\n[dim]{t('cli_tip1', lang)}[/]")
    console.print(f"[dim]{t('cli_tip2', lang)}[/]")


def build_parser():
    from . import __version__
    parser = argparse.ArgumentParser(
        prog="network-tui",
        description="Network-TUI — Network scanner (TUI + CLI) / ตัวสแกนเครือข่าย",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples / ตัวอย่าง:
  network-tui                      # open TUI / เปิด TUI
  network-tui --cli                # scan and print table
  network-tui --cli --export auto  # scan and export CSV
  network-tui --cli -i Wi-Fi       # choose interface / เลือก interface
  network-tui --cli --lang th      # CLI in Thai / CLI ภาษาไทย
        """
    )
    parser.add_argument("--cli", action="store_true", help="run in CLI mode, no TUI / รันแบบ CLI ไม่เปิด TUI")
    parser.add_argument("-i", "--interface", type=str, default=None, help="interface name or IP / ชื่อ interface หรือ IP")
    parser.add_argument("--timeout", type=int, default=700, help="ping timeout per host in ms, 200-5000 (default 700)")
    parser.add_argument("--workers", type=int, default=80, help="parallel scan threads, 10-200 (default 80)")
    parser.add_argument("--export", type=str, nargs="?", const="auto", default=None, help="export CSV/JSON (filename or auto)")
    parser.add_argument("--list-interfaces", action="store_true", help="list interfaces and exit / แสดง interfaces แล้วออก")
    parser.add_argument("--lang", type=str, choices=["th", "en"], default=None, help="language: th or en (default: saved setting)")
    parser.add_argument("--mask", action="store_true", help="mask IP/MAC/hostnames in displayed table (for screenshots; export keeps real data)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    lang = resolve_lang(args.lang)

    # validate กันพิมพ์ผิดแล้วสแกนช้า/พัง
    if args.timeout < 200 or args.timeout > 5000:
        parser.error("--timeout must be 200-5000 ms")
    if args.workers < 10 or args.workers > 200:
        parser.error("--workers must be 10-200")

    if args.list_interfaces:
        from .scanner import get_network_infos
        from rich.console import Console
        from rich.table import Table
        console = Console(legacy_windows=False)
        infos = get_network_infos()
        t = Table(title="Network Interfaces", header_style="bold cyan")
        t.add_column("Interface", overflow="fold")
        t.add_column("IP", overflow="fold")
        t.add_column("Netmask", overflow="fold")
        t.add_column("CIDR", overflow="fold")
        t.add_column("Gateway", overflow="fold")
        t.add_column("MAC", overflow="fold")
        for inf in infos:
            t.add_row(inf.interface, inf.local_ip, inf.netmask, inf.cidr, inf.gateway or "-", inf.mac or "-")
        console.print(t)
        return

    if args.cli or args.export:
        run_cli_scan(args, lang=lang)
    else:
        run_tui()


if __name__ == "__main__":
    main()
