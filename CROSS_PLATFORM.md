# Cross-platform preview

This branch adds a new CLI around the existing detector and licensed logos.
It is a foundation, not feature parity with Fastfetch.

## Install from a checkout

Python 3.10+ is required. No runtime dependencies, root, WMIC or PowerShell are required.

```sh
python -m pip install .
viofetch --theme mint
viofetch --layout auto
viofetch --fields OS,Kernel,CPU,Memory,Storage
viofetch --json --fields OS,CPU
viofetch --list-fields
```

On Windows use `py -m pip install .` if `python` is not available. Restart the terminal or use `python -m viofetch_cli` if the scripts directory is not on PATH.

In Termux install Python first with `pkg install python`; do not replace Termux's managed pip. From a checkout you can run `python -m viofetch_cli` without installing the package.

Themes: `violet`, `mint`, `rose`, `system`. `NO_COLOR` is respected in auto mode; `--plain` always disables styling. Automatic layout stacks the logo above the information when side-by-side output will not fit. Very long values can still wrap; this is not an interactive terminal UI.

## Windows

RAM uses GlobalMemoryStatusEx; uptime uses GetTickCount64; CPU reads the standard registry description. Storage reports the home filesystem. Host currently shows the hostname, not a motherboard/model. Shell is a best-effort environment label, not process-tree detection. Battery is not yet implemented on Windows. No hardware serial numbers are collected.

## Compatibility

The original `python viofetch.py` entry point and its API remain available as the legacy CLI. New options and Windows probes use the installed `viofetch` command or `python -m viofetch_cli`. Existing 0.2.0 version is intentionally retained until a release is approved.

CI runs unit tests, installation and CLI smoke tests on Ubuntu and Windows, Python 3.10, 3.12 and 3.13. CI is not a substitute for real Termux-device testing.

Next steps: review real Windows output, test Termux, then unify the entry points; add config validation, optional GPU/display/package modules, and custom logos as separate changes with tests.
