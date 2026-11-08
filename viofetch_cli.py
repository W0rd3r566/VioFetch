"""Cross-platform VioFetch CLI; standard library only.

Keep the original detector and licensed logos in viofetch.py. This module adds
native Windows probes and presentation controls without changing its public API.
"""
from __future__ import annotations

import argparse
import ctypes
import getpass
import json
import os
import platform
import re
import shutil
import sys
import unicodedata
from pathlib import Path
from typing import Mapping, Sequence

import viofetch as core

THEMES = {
    "violet": ("\033[38;5;141m", "\033[38;5;183m"),
    "mint": ("\033[38;5;79m", "\033[38;5;159m"),
    "rose": ("\033[38;5;211m", "\033[38;5;225m"),
    "system": ("\033[36m", "\033[1m"),
}
FIELDS = ("OS", "Host", "Kernel", "Uptime", "Shell", "Terminal", "CPU",
          "Architecture", "Memory", "Storage", "Python", "Battery")
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def cell_width(text: str) -> int:
    """Conservative terminal width, including CJK and combining characters."""
    return sum(0 if unicodedata.combining(c) else
               2 if unicodedata.east_asian_width(c) in {"W", "F"} else 1
               for c in ANSI.sub("", text))


def enable_windows_ansi() -> bool:
    """Enable VT on the output console; never assume redirected output is a TTY."""
    if os.name != "nt":
        return True
    try:
        kernel = ctypes.windll.kernel32
        handle = kernel.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        return bool(kernel.GetConsoleMode(handle, ctypes.byref(mode)) and
                    kernel.SetConsoleMode(handle, mode.value | 0x0004))
    except (AttributeError, OSError):
        return False


def windows_memory() -> str | None:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [("length", ctypes.c_uint32), ("load", ctypes.c_uint32)] + [
            (name, ctypes.c_uint64) for name in (
                "total_phys", "avail_phys", "total_page", "avail_page",
                "total_virtual", "avail_virtual", "avail_extended")]
    try:
        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return None
        return f"{core.format_bytes(status.total_phys - status.avail_phys)} / {core.format_bytes(status.total_phys)}"
    except (AttributeError, OSError):
        return None


def windows_uptime() -> str | None:
    try:
        tick = ctypes.windll.kernel32.GetTickCount64
        tick.restype = ctypes.c_uint64
        return core.format_duration(tick() / 1000)
    except (AttributeError, OSError):
        return None


def windows_cpu() -> str:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
            return str(winreg.QueryValueEx(key, "ProcessorNameString")[0]).strip()
    except (ImportError, OSError):
        return os.environ.get("PROCESSOR_IDENTIFIER") or platform.machine() or "Unknown"


def collect_info() -> dict[str, str]:
    if platform.system() != "Windows":
        return core.collect_info()
    try:
        user = getpass.getuser()
    except (KeyError, OSError):
        user = os.environ.get("USERNAME", "user")
    # No WMIC, PowerShell, subprocess shell, admin privileges, or external packages.
    info = {
        "User": f"{user}@{platform.node() or 'localhost'}",
        "OS": f"Windows {platform.win32_ver()[0] or platform.release()}",
        "Host": platform.node() or "Unknown",
        "Kernel": platform.version(),
        "Uptime": windows_uptime() or "Unknown",
        "Shell": Path(os.environ.get("SHELL") or os.environ.get("COMSPEC", "cmd.exe")).name,
        "Terminal": "Windows Terminal" if os.environ.get("WT_SESSION") else os.environ.get("TERM_PROGRAM", "Windows console"),
        "CPU": windows_cpu(),
        "Architecture": platform.machine() or "Unknown",
        "Memory": windows_memory() or "Unavailable",
        "Storage": core.get_storage() or "Unavailable",
        "Python": platform.python_version(),
    }
    return info


def parse_fields(value: str) -> list[str]:
    known = {name.casefold(): name for name in FIELDS}
    result = []
    for part in value.split(","):
        key = part.strip().casefold()
        if key not in known:
            raise argparse.ArgumentTypeError(f"Unknown field {part!r}. Choose: {', '.join(FIELDS)}")
        if known[key] not in result:
            result.append(known[key])
    return result


def render(info: Mapping[str, str], *, logo_name: str = "auto", layout: str = "auto",
           width: int = 80, color: bool = False, theme: str = "violet",
           fields: Sequence[str] | None = None, no_logo: bool = False) -> str:
    primary, accent = THEMES[theme]
    def tint(text: str, shade: str) -> str:
        return core.colorize(text, shade, color)
    user = info.get("User", "user@host")
    selected = list(fields) if fields is not None else [k for k in info if k != "User"]
    rows = [(key, info[key]) for key in selected if key in info and key != "User"]
    label_width = max((cell_width(key) for key, _ in rows), default=0)
    lines = [tint(user, accent), tint("─" * max(8, cell_width(user)), core.GRAY)]
    for key, value in rows:
        lines.append(tint(key + " " * (label_width - cell_width(key)), primary) + "  " + value)
    if no_logo:
        return "\n".join(lines)
    logo = core.select_logo(info, requested=logo_name)
    logo_width = max((cell_width(line) for line in logo), default=0)
    info_width = max((cell_width(line) for line in lines), default=0)
    if layout == "auto":
        layout = "left" if logo_width + 3 + info_width <= width else "top"
    if layout == "top":
        return "\n".join([*(tint(line, primary) for line in logo), "", *lines])
    combined = []
    for index in range(max(len(logo), len(lines))):
        art = logo[index] if index < len(logo) else ""
        text = lines[index] if index < len(lines) else ""
        combined.append(tint(art, primary) + " " * (logo_width - cell_width(art) + 3) + text)
    return "\n".join(combined)


def build_parser() -> argparse.ArgumentParser:
    parser = core.build_parser()
    parser.description = "VioFetch: Termux, Linux and native Windows system summary."
    parser.add_argument("--theme", choices=tuple(THEMES), default="violet")
    parser.add_argument("--layout", choices=("auto", "left", "top"), default="auto",
                        help="auto stacks logo above information on narrow terminals")
    parser.add_argument("--fields", type=parse_fields, metavar="OS,CPU,Memory",
                        help="select and order fields (case-insensitive)")
    parser.add_argument("--list-fields", action="store_true", help="list supported field names")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list_fields:
        print("\n".join(FIELDS))
        return 0
    info = collect_info()
    if args.fields is not None:
        info = {"User": info.get("User", "user@host"),
                **{field: info[field] for field in args.fields if field in info}}
    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return 0
    color = not args.plain and (args.color == "always" or
            (args.color == "auto" and sys.stdout.isatty() and "NO_COLOR" not in os.environ))
    if color:
        color = enable_windows_ansi()
    print(render(info, logo_name=args.logo, layout=args.layout,
                 width=shutil.get_terminal_size((80, 24)).columns, color=color,
                 theme=args.theme, fields=args.fields, no_logo=args.no_logo or args.plain))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
