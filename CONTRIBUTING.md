# Contributing to VioFetch

Thanks for helping improve VioFetch! The first release targets Termux on Android, so real-device reports are especially useful.

## Before opening an issue

- Use the latest project version you have available.
- Include the Android version, device architecture, Termux version, and Python version when relevant.
- Paste the command you ran and the complete error output.
- Remove private information from logs before posting them.
- Do not report a missing optional value as a crash if the program completed successfully.

## Development setup

VioFetch currently uses only the Python standard library.

```bash
python -m unittest discover -s tests -v
python viofetch.py --plain
python viofetch.py --json
```

## Pull requests

- Keep the default output minimal and readable on narrow mobile terminals.
- Missing commands, unreadable files, and unsupported device properties should not crash the program.
- Do not add mandatory dependencies without discussing the trade-off in an issue.
- Add or update tests when changing parsing or formatting behavior.
- Keep Termux support working before adding platform-specific code for other systems.

## Scope

VioFetch is independently implemented. Do not copy source code from projects whose licenses or attribution requirements are incompatible with the contribution. Inspiration and compatibility references should be credited in documentation.
