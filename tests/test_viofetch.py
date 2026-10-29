import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import viofetch


class FormatTests(unittest.TestCase):
    def test_format_bytes(self):
        self.assertEqual(viofetch.format_bytes(0), "0 B")
        self.assertEqual(viofetch.format_bytes(1024), "1.0 KiB")
        self.assertEqual(viofetch.format_bytes(1024**3), "1.0 GiB")

    def test_format_duration(self):
        self.assertEqual(viofetch.format_duration(59), "0m")
        self.assertEqual(viofetch.format_duration(3661), "1h 1m")
        self.assertEqual(viofetch.format_duration(90061), "1d 1h 1m")

    def test_meminfo_with_available(self):
        data = "MemTotal: 8000 kB\nMemAvailable: 3000 kB\n"
        self.assertEqual(viofetch.parse_meminfo(data), (8000 * 1024, 3000 * 1024))

    def test_meminfo_falls_back_to_free(self):
        data = "MemTotal: 8000 kB\nMemFree: 2000 kB\n"
        self.assertEqual(viofetch.parse_meminfo(data), (8000 * 1024, 2000 * 1024))

    def test_meminfo_rejects_incomplete_data(self):
        self.assertIsNone(viofetch.parse_meminfo("MemTotal: 8000 kB\n"))

    def test_cpuinfo_x86(self):
        self.assertEqual(
            viofetch.parse_cpuinfo("processor: 0\nmodel name : Example CPU 9000\n"),
            "Example CPU 9000",
        )

    def test_cpuinfo_arm(self):
        self.assertEqual(
            viofetch.parse_cpuinfo("Processor : AArch64 Processor rev 1\nHardware : Example Board\n"),
            "Example Board",
        )

    def test_termux_detection(self):
        self.assertTrue(viofetch.is_termux({"PREFIX": "/data/data/com.termux/files/usr"}, "/usr/bin/python"))
        self.assertTrue(viofetch.is_termux({"TERMUX_VERSION": "0.118"}, "/usr/bin/python"))
        self.assertFalse(viofetch.is_termux({}, "/usr/bin/python"))

    def test_render_can_be_plain(self):
        output = viofetch.render({"User": "test@device", "OS": "Android / Termux"}, no_logo=True, color=False)
        self.assertIn("test@device", output)
        self.assertIn("OS", output)
        self.assertNotIn("\033[", output)

    def test_android_logo_selected(self):
        logo = viofetch.select_logo({"OS": "Android 17 (API 37) / Termux"})
        self.assertIn("ANDROID", logo[-1])
        self.assertNotIn("VIOFETCH", logo[-1])

    def test_linux_distribution_logos(self):
        cases = {
            "CachyOS": "CACHYOS",
            "Arch Linux": "ARCH",
            "Ubuntu 26.04": "UBUNTU",
            "Debian GNU/Linux": "DEBIAN",
            "Fedora Linux": "FEDORA",
            "Microsoft Windows 11": "WINDOWS",
            "macOS": "macOS",
        }
        for os_name, expected in cases.items():
            with self.subTest(os_name=os_name):
                self.assertIn(expected, viofetch.select_logo({"OS": os_name})[-1])

    def test_unknown_os_uses_viofetch_mark(self):
        self.assertEqual(
            viofetch.select_logo({"OS": "Unknown OS"}),
            viofetch.LOGO,
        )


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "viofetch.py"), *args],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_version(self):
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0)
        self.assertIn(viofetch.__version__, result.stdout)

    def test_json_output(self):
        result = self.run_cli("--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIn("OS", data)
        self.assertIn("Python", data)

    def test_plain_output(self):
        result = self.run_cli("--plain")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("\033[", result.stdout)
        self.assertIn("OS", result.stdout)


if __name__ == "__main__":
    unittest.main()
