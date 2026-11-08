import json
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO
import viofetch_cli as cli


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.info = {"User": "test@host", "OS": "CachyOS", "CPU": "Test CPU", "Memory": "1 GiB / 8 GiB"}

    def test_fields(self):
        self.assertEqual(cli.parse_fields("cpu, OS, cpu"), ["CPU", "OS"])

    def test_unknown_field(self):
        with self.assertRaises(cli.argparse.ArgumentTypeError):
            cli.parse_fields("secret")

    def test_cell_width(self):
        self.assertEqual(cli.cell_width("\033[31mA界e\u0301\033[0m"), 4)

    def test_auto_narrow_stacks(self):
        self.assertIn("\n\ntest@host", cli.render(self.info, width=25))

    def test_auto_wide_left(self):
        self.assertNotIn("\n\ntest@host", cli.render(self.info, width=200))

    def test_selected_order(self):
        result = cli.render(self.info, no_logo=True, fields=["Memory", "OS"])
        self.assertNotIn("Test CPU", result)
        self.assertLess(result.index("Memory"), result.index("OS"))

    def test_all_themes_plain(self):
        for theme in cli.THEMES:
            self.assertNotIn("\033", cli.render(self.info, theme=theme))
            self.assertIn("\033", cli.render(self.info, theme=theme, color=True))

    def test_json_selection(self):
        output = StringIO()
        with patch.object(cli, "collect_info", return_value=self.info), redirect_stdout(output):
            self.assertEqual(cli.main(["--json", "--fields", "OS"]), 0)
        self.assertEqual(json.loads(output.getvalue()), {"User": "test@host", "OS": "CachyOS"})

    def test_list_fields_skips_detection(self):
        with patch.object(cli, "collect_info") as collect, redirect_stdout(StringIO()):
            cli.main(["--list-fields"])
        collect.assert_not_called()

    def test_windows_avoids_termux_collector(self):
        with (patch.object(cli.platform, "system", return_value="Windows"),
              patch.object(cli.platform, "win32_ver", return_value=("11", "", "", "")),
              patch.object(cli, "windows_memory", return_value="2 GiB / 8 GiB"),
              patch.object(cli, "windows_uptime", return_value="1h 0m"),
              patch.object(cli, "windows_cpu", return_value="Test CPU"),
              patch.object(cli.core, "collect_info") as old):
            info = cli.collect_info()
        old.assert_not_called()
        self.assertEqual(info["OS"], "Windows 11")
        self.assertEqual(info["Memory"], "2 GiB / 8 GiB")

    def test_linux_preserves_detector(self):
        with patch.object(cli.platform, "system", return_value="Linux"), patch.object(cli.core, "collect_info", return_value=self.info):
            self.assertEqual(cli.collect_info(), self.info)


if __name__ == "__main__":
    unittest.main()
