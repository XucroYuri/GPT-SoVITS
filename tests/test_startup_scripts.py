import unittest
from pathlib import Path


class StartupScriptsTests(unittest.TestCase):
    def test_windows_scripts_have_separate_single_service_entries(self):
        root = Path(__file__).resolve().parents[1]
        expectations = {
            "启动_训练WebUI.bat": ["tools\\startup_check.py --mode train", "tools\\run_with_bootstrap.py -- webui.py zh_CN", "logs\\startup"],
            "启动_推理WebUI.bat": [
                "tools\\startup_check.py --mode infer-webui",
                "-s -u tools\\run_with_bootstrap.py -- GPT_SoVITS\\inference_webui.py zh_CN",
                "logs\\startup",
            ],
            "启动_API服务.bat": ["tools\\startup_check.py --mode api", "-s -u tools\\run_with_bootstrap.py -- api_v2.py", "logs\\startup"],
        }

        for script_name, markers in expectations.items():
            with self.subTest(script=script_name):
                script = root / script_name
                self.assertTrue(script.exists(), f"{script_name} should exist")
                content = script.read_text(encoding="utf-8")
                for marker in markers:
                    self.assertIn(marker, content)

    def test_windows_scripts_use_crlf_line_endings(self):
        root = Path(__file__).resolve().parents[1]
        script_names = [
            "启动_训练WebUI.bat",
            "启动_推理WebUI.bat",
            "启动_API服务.bat",
            "开始训练.bat",
            "运行_统一推理WebUI.bat",
            "运行_自动开启接口服务.bat",
        ]

        for script_name in script_names:
            with self.subTest(script=script_name):
                data = (root / script_name).read_bytes()
                self.assertNotIn(b"\r\r\n", data)
                self.assertEqual(data.count(b"\n"), data.count(b"\r\n"))


if __name__ == "__main__":
    unittest.main()
