import json
import tempfile
import unittest
from pathlib import Path

from tools import build_portable_package as portable


class PortablePackageTests(unittest.TestCase):
    def test_root_packaging_script_calls_portable_builder(self):
        root = Path(__file__).resolve().parents[1]
        script = root / "打包_绿色版.bat"
        self.assertTrue(script.exists())
        content = script.read_text(encoding="utf-8")
        self.assertIn("tools\\build_portable_package.py", content)

        data = script.read_bytes()
        self.assertEqual(data.count(b"\n"), data.count(b"\r\n"))

    def test_exclusion_rules_drop_training_outputs_and_legacy_entries(self):
        excluded = [
            "logs/白泽TTS新-20260611/train.log",
            "logs/startup/infer-webui.log",
            "GPT_weights_v2ProPlus/白泽TTS新-20260611-e50.ckpt",
            "SoVITS_weights_v2ProPlus/白泽TTS新-20260611_e24_s264.pth",
            "output/asr_opt/白泽TTS新-20260611/白泽TTS新.list",
            "output/slicer_opt/example.wav",
            "tmp/gradio/cache.bin",
            "TEMP/runtime.tmp",
            "tests/test_startup_check.py",
            "__pycache__/config.cpython-312.pyc",
            "character_map.json",
            "app.py",
            "api.py",
            "开始训练.bat",
            "运行_统一推理WebUI.bat",
            "运行_自动开启接口服务.bat",
        ]
        included = [
            "GPT_SoVITS/inference_webui.py",
            "GPT_SoVITS/pretrained_models/s1v3.ckpt",
            "GPT_SoVITS/pretrained_models/v2Pro/s2Gv2ProPlus.pth",
            "py312/python.exe",
            "tools/startup_check.py",
            "api_v2.py",
            "webui.py",
            "启动_推理WebUI.bat",
            "参考音频/example.wav",
        ]

        for rel_path in excluded:
            with self.subTest(path=rel_path):
                self.assertTrue(portable.should_exclude(rel_path), rel_path)
        for rel_path in included:
            with self.subTest(path=rel_path):
                self.assertFalse(portable.should_exclude(rel_path), rel_path)

    def test_staging_cleanup_writes_pretrained_weight_config_and_menu(self):
        with tempfile.TemporaryDirectory() as temp:
            staging = Path(temp)
            portable.prepare_staging_overrides(staging)

            weight = json.loads((staging / "weight.json").read_text(encoding="utf-8"))
            self.assertEqual(
                weight,
                {
                    "GPT": {"v2": "GPT_SoVITS/pretrained_models/s1v3.ckpt"},
                    "SoVITS": {"v2": "GPT_SoVITS/pretrained_models/v2Pro/s2Gv2ProPlus.pth"},
                },
            )
            self.assertFalse((staging / "character_map.json").exists())

            menu = (staging / "启动菜单.bat").read_text(encoding="utf-8")
            self.assertIn("1 推理WebUI(9872)", menu)
            self.assertIn("2 训练WebUI(9874)", menu)
            self.assertIn("3 API服务(9880/docs)", menu)
            self.assertIn("call \"启动_推理WebUI.bat\"", menu)
            self.assertIn("call \"启动_训练WebUI.bat\"", menu)
            self.assertIn("call \"启动_API服务.bat\"", menu)

            menu_bytes = (staging / "启动菜单.bat").read_bytes()
            self.assertEqual(menu_bytes.count(b"\n"), menu_bytes.count(b"\r\n"))

    def test_runtime_empty_directories_are_created_without_training_weights(self):
        with tempfile.TemporaryDirectory() as temp:
            staging = Path(temp)
            portable.prepare_staging_overrides(staging)

            for rel_path in portable.RUNTIME_EMPTY_DIRS:
                with self.subTest(path=rel_path):
                    directory = staging / rel_path
                    self.assertTrue(directory.is_dir(), rel_path)
                    self.assertEqual(list(directory.iterdir()), [])

    def test_staging_rewrites_users_pth_to_portable_relative_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            staging = Path(temp)
            site_packages = staging / "py312" / "Lib" / "site-packages"
            site_packages.mkdir(parents=True)
            (site_packages / "users.pth").write_text(
                "J:\\TTS\\GPT-SoVITS\\GPT-SoVITS-v2_ProPlus-hc-dev\\GPT-SoVITS-v2_ProPlus-hc-dev\n",
                encoding="utf-8",
            )

            portable.prepare_staging_overrides(staging)

            content = (site_packages / "users.pth").read_text(encoding="utf-8")
            self.assertNotIn("J:\\TTS\\GPT-SoVITS", content)
            self.assertIn("../../../GPT_SoVITS", content)
            self.assertIn("../../../tools", content)

    def test_remove_if_exists_tolerates_files_that_disappear_during_cleanup(self):
        original_rmtree = portable.shutil.rmtree
        temp = Path(tempfile.mkdtemp())
        try:
            parent = temp
            target = parent / "staging"
            target.mkdir()

            def stale_rmtree(_path):
                raise FileNotFoundError("already gone")

            portable.shutil.rmtree = stale_rmtree
            portable._remove_if_exists(target, parent)
        finally:
            portable.shutil.rmtree = original_rmtree
            if temp.exists():
                portable.shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
