#!/usr/bin/env python3
"""VioFetch: a minimal, dependency-free system summary for Termux.

This is an independent implementation inspired by the system-summary format
popularized by Neofetch. It does not reuse Neofetch source code.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Mapping, Sequence

__version__ = "0.1.0"

# VioFetch's small violet/gray palette. Colors are used only in terminal output.
VIOLET = "\033[38;5;141m"
LAVENDER = "\033[38;5;183m"
GRAY = "\033[38;5;245m"
BOLD = "\033[1m"
RESET = "\033[0m"

LOGO = (
    "      /\\",
    "     /  \\",
    "    / /\\ \\",
    "   / /  \\ \\",
    "  /_/____\\_\\",
    "    VIOFETCH",
)


def run_command(args: Sequence[str], timeout: float = 1.2) -> str | None:
    """Run a command safely; unavailable commands and timeouts are non-fatal."""
    try:
        result = subprocess.run(
            list(args),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = result.stdout.strip()
    return output or None


def read_text(path: str | Path) -> str | None:
    """Read a text file without letting missing or restricted files stop VioFetch."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeError):
        return None


def getprop(name: str) -> str | None:
    """Read one Android property when the getprop command exists."""
    return run_command(["getprop", name], timeout=0.8)


def is_termux(environ: Mapping[str, str] | None = None, executable: str | None = None) -> bool:
    """Detect Termux without relying on a particular username or CPU type."""
    env = os.environ if environ is None else environ
    exe = sys.executable if executable is None else executable
    prefix = env.get("PREFIX", "")
    return bool(
        env.get("TERMUX_VERSION")
        or "/com.termux/" in prefix
        or prefix.endswith("/com.termux/files/usr")
        or "/com.termux/" in exe
    )


def parse_meminfo(contents: str) -> tuple[int, int] | None:
    """Return (total_bytes, available_bytes) from Linux /proc/meminfo."""
    values: dict[str, int] = {}
    for line in contents.splitlines():
        match = re.match(r"^(MemTotal|MemAvailable|MemFree):\s+(\d+)\s+kB", line)
        if match:
            values[match.group(1)] = int(match.group(2)) * 1024
    total = values.get("MemTotal")
    available = values.get("MemAvailable", values.get("MemFree"))
    if total is None or available is None or total <= 0:
        return None
    return total, min(max(available, 0), total)


def format_bytes(num_bytes: int | float) -> str:
    """Format a byte count with binary units without excessive precision."""
    value = max(0.0, float(num_bytes))
    units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PiB"


def format_duration(seconds: float) -> str:
    """Format uptime as a compact, readable duration."""
    total = max(0, int(seconds))
    days, remainder = divmod(total, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def parse_cpuinfo(contents: str) -> str | None:
    """Find a human-readable CPU label in common ARM and x86 cpuinfo formats."""
    preferred = ("model name", "hardware", "processor", "cpu model")
    found: dict[str, str] = {}
    for line in contents.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = " ".join(value.strip().split())
        if value and key in preferred and key not in found:
            found[key] = value
    for key in preferred:
        value = found.get(key)
        if value and value.lower() not in {"unknown", "generic", "0"}:
            return value
    return None


def format_battery() -> str | None:
    """Read battery details if the optional Termux:API command is available."""
    if not is_termux() or shutil.which("termux-battery-status") is None:
        return None
    output = run_command(["termux-battery-status"], timeout=1.8)
    if not output:
        return None
    try:
        payload = json.loads(output)
    except (json.JSONDecodeError, TypeError):
        return None
    percentage = payload.get("percentage")
    status = payload.get("status")
    if not isinstance(percentage, (int, float)):
        return None
    result = f"{int(percentage)}%"
    if isinstance(status, str) and status.strip():
        result += f" ({status.strip().lower()})"
    return result


def os_description(termux: bool) -> str:
    """Get an OS name, preferring the Android properties on Termux."""
    if termux:
        release = getprop("ro.build.version.release")
        sdk = getprop("ro.build.version.sdk")
        name = f"Android {release}" if release else "Android"
        if sdk and sdk.isdigit():
            name += f" (API {sdk})"
        return name + " / Termux"

    try:
        data = platform.freedesktop_os_release()
        name = data.get("PRETTY_NAME") or data.get("NAME")
        if name:
            return name
    except (AttributeError, OSError):
        pass
    return f"{platform.system() or 'Unknown'} {platform.release()}".strip()


def get_host(termux: bool) -> str:
    """Get a readable host/device label, using Android properties on Termux."""
    if termux:
        manufacturer = getprop("ro.product.manufacturer")
        model = getprop("ro.product.model")
        parts = [part.strip() for part in (manufacturer, model) if part and part.strip()]
        if parts:
            # Avoid duplicate brand text, e.g. Google Google Pixel.
            if len(parts) == 2 and parts[0].lower() in parts[1].lower():
                return parts[1]
            return " ".join(parts)
    return platform.node() or socket.gethostname() or "Unknown"


def get_cpu(termux: bool) -> str:
    """Detect a CPU/SoC label without assuming one architecture."""
    if termux:
        soc = getprop("ro.soc.model")
        if soc and soc.lower() not in {"unknown", "", "0"}:
            return soc
        hardware = getprop("ro.hardware")
        # Some Android builds expose only a board or chipset codename here.
        if hardware and hardware.lower() not in {"unknown", "generic", "qcom"}:
            return hardware
    info = read_text("/proc/cpuinfo")
    if info:
        parsed = parse_cpuinfo(info)
        if parsed:
            return parsed
    processor = platform.processor()
    return processor or platform.machine() or "Unknown"


def get_memory() -> str | None:
    """Return used/total RAM when /proc/meminfo is readable."""
    contents = read_text("/proc/meminfo")
    parsed = parse_meminfo(contents) if contents else None
    if not parsed:
        return None
    total, available = parsed
    used = max(0, total - available)
    return f"{format_bytes(used)} / {format_bytes(total)}"


def get_uptime() -> str | None:
    """Read Linux uptime from /proc."""
    contents = read_text("/proc/uptime")
    if contents:
        try:
            return format_duration(float(contents.split()[0]))
        except (ValueError, IndexError):
            pass
    return None


def get_storage() -> str | None:
    """Report free and total space for the user's home filesystem."""
    try:
        usage = shutil.disk_usage(Path.home())
    except OSError:
        return None
    return f"{format_bytes(usage.free)} free / {format_bytes(usage.total)}"


def get_shell() -> str:
    shell = os.environ.get("SHELL", "")
    return Path(shell).name if shell else "Unknown"


def collect_info() -> dict[str, str]:
    """Collect all currently supported fields, omitting unavailable values."""
    termux = is_termux()
    username = getpass.getuser() or os.environ.get("USER") or "user"
    hostname = socket.gethostname() or "localhost"
    info: dict[str, str] = {
        "User": f"{username}@{hostname}",
        "OS": os_description(termux),
        "Host": get_host(termux),
        "Kernel": run_command(["uname", "-r"]) or platform.release() or "Unknown",
        "Uptime": get_uptime() or "Unknown",
        "Shell": get_shell(),
        "Terminal": "Termux" if termux else (os.environ.get("TERM", "Unknown")),
        "CPU": get_cpu(termux),
        "Architecture": platform.machine() or "Unknown",
        "Memory": get_memory() or "Unavailable",
        "Storage": get_storage() or "Unavailable",
        "Python": platform.python_version(),
    }
    battery = format_battery()
    if battery:
        info["Battery"] = battery
    return info


def colorize(text: str, color: str, enabled: bool) -> str:
    return f"{color}{text}{RESET}" if enabled else text


def render(info: Mapping[str, str], *, no_logo: bool = False, color: bool = True) -> str:
    """Render Neofetch-style logo and system fields with a restrained palette."""
    user = info.get("User", "user@host")
    fields = [(key, value) for key, value in info.items() if key != "User"]
    header = colorize(user, BOLD + LAVENDER, color)
    divider = colorize("─" * max(8, len(user)), GRAY, color)
    lines = [header, divider]
    for key, value in fields:
        label = colorize(f"{key:<12}", VIOLET, color)
        lines.append(f"{label} {value}")

    if no_logo:
        return "\n".join(lines)

    logo_lines = [colorize(line, VIOLET, color) for line in LOGO]
    width = max(len(line) for line in LOGO)
    height = max(len(logo_lines), len(lines))
    combined: list[str] = []
    for index in range(height):
        logo = logo_lines[index] if index < len(logo_lines) else ""
        line = lines[index] if index < len(lines) else ""
        # ANSI escape sequences have already been applied to the display copy,
        # so pad using the original logo width instead of len(logo).
        padding = " " * max(2, width - (len(LOGO[index]) if index < len(LOGO) else 0) + 3)
        combined.append(logo + padding + line)
    return "\n".join(combined)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="viofetch",
        description="Minimal violet system information for Termux and Linux.",
    )
    parser.add_argument("--version", action="version", version=f"VioFetch {__version__}")
    parser.add_argument("--no-logo", action="store_true", help="show information without the VioFetch logo")
    parser.add_argument("--plain", action="store_true", help="plain output without logo or colors")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help="color output (default: auto)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    info = collect_info()

    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return 0

    if args.color == "always":
        use_color = True
    elif args.color == "never" or args.plain:
        use_color = False
    else:
        use_color = sys.stdout.isatty() and "NO_COLOR" not in os.environ

    output = render(info, no_logo=args.no_logo or args.plain, color=use_color)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
