# VioFetch

**A minimal, violet-styled system fetch for Termux.** VioFetch prints a compact system summary in the terminal, inspired by the system-summary format popularized by Neofetch. It is an independent implementation and does not reuse Neofetch source code.

**Current target:** Termux on Android. Other Linux distributions are a secondary best-effort fallback in this initial preview. Native Windows/macOS support is not claimed yet.

## Preview

```text
       \  |  /       test@localhost
        \ | /        ──────────────
       .-"""-.         OS           Android 17 / Termux
      /  o o  \       Host         Google Pixel
     |    ^    |       Kernel       6.x.x-android
     |         |       Uptime       2h 14m
      \_______/       Shell        bash
     /|  | |  |\       Terminal     Termux
    /_|__|_|__|_\     CPU          Tensor G4
       /_/ \_\        Architecture aarch64
       ANDROID          Memory       3.2 GiB / 7.5 GiB
                        Storage      18.0 GiB free / 110.0 GiB
                        Python       3.x
```

The values above are illustrative, not a real device report. The battery line appears only when the optional Termux:API command is available.

## Requirements

- Termux from a supported installation source
- Python 3.10 or newer
- No third-party Python packages

## Run in Termux

```bash
pkg update
pkg install python
python viofetch.py
```

To run a local copy, put `viofetch.py` in a folder and execute it with Python. No root access is required.

### Optional battery information

Battery data is optional. Install both the **Termux:API Android app** and its Termux package if you want VioFetch to show battery percentage and status:

```bash
pkg install termux-api
```

The API app must be installed separately, and its installation source/signature must match the main Termux app. If it is missing or access fails, VioFetch continues without the battery line. See [Termux:API](https://github.com/termux/termux-api).

## Usage

```bash
python viofetch.py             # normal output
python viofetch.py --plain     # no logo or colors
python viofetch.py --no-logo   # information without the logo
python viofetch.py --color never
python viofetch.py --color always
python viofetch.py --json      # machine-readable JSON
python viofetch.py --version
python viofetch.py --help
```

`--json` prints collected values without terminal escape codes. `--color auto` (the default) enables colors only in an interactive terminal and respects `NO_COLOR`.

## What it detects today

- Android release and API level on Termux
- Device manufacturer/model
- Kernel and architecture
- CPU/SoC label when Android exposes one
- Uptime and RAM from `/proc`
- Free and total storage for the home filesystem
- Shell, terminal, and Python versions
- Optional battery status through Termux:API

Android device properties differ by vendor and firmware. Some fields may show `Unknown` or be omitted when they are not available. VioFetch does not require root and does not change system settings.

## Development

Run the test suite with the Python standard library:

```bash
python -m unittest discover -s tests -v
```

## Roadmap

- [x] Termux-first prototype with no third-party Python dependencies
- [x] Violet/gray terminal styling and OS-specific ASCII logos
- [x] JSON output and no-color modes
- [x] Basic automated tests and GitHub Actions
- [ ] Test on more Termux devices and Android versions
- [x] Add ASCII logos for Android and major operating systems/distributions
- [ ] Add configurable fields and custom logo selection
- [ ] Improve Linux distribution detection
- [ ] Add and test native Windows support
- [ ] Add packaging and installation helpers

## License

MIT. See [LICENSE](LICENSE).

---

## Русский

**VioFetch** — минималистичная системная сводка для Termux с фиолетово-серым оформлением. Показывает основные сведения об Android-устройстве прямо в терминале. Проект вдохновлён форматом Neofetch, но реализован независимо, без копирования его исходного кода.

**Первая цель — Termux на Android.** Логотип выбирается автоматически: доступны варианты для Android, CachyOS, Arch Linux, Ubuntu, Debian, Fedora, Manjaro, Windows, macOS и общего Linux. На других Linux-системах возможен базовый вывод, а полноценная нативная поддержка Windows/macOS пока не заявляется.

### Запуск

```bash
pkg update
pkg install python
python viofetch.py
```

Сторонние Python-библиотеки и root не нужны. Для дополнительной строки с батареей можно установить пакет `termux-api` и отдельное приложение Termux:API. Если API недоступен, скрипт просто пропустит эту строку.

### Параметры

- `--plain` — вывод без логотипа и цветов
- `--no-logo` — убрать логотип
- `--color auto|always|never` — режим цветов
- `--json` — вывести данные в JSON
- `--version` — версия
- `--help` — справка

### Проверка тестов

```bash
python -m unittest discover -s tests -v
```

Поля, недоступные конкретной версии Android или производителю, могут отображаться как `Unknown` либо не выводиться. VioFetch не требует root-доступа и ничего не меняет в системе.
