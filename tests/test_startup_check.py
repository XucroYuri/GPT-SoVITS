import json
import tempfile
import unittest
from pathlib import Path


class StartupCheckTests(unittest.TestCase):
    def test_weight_json_reports_missing_weight_with_pretrained_hint(self):
        from tools import startup_check

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pretrained = root / "GPT_SoVITS" / "pretrained_models" / "v2Pro"
            pretrained.mkdir(parents=True)
            (pretrained / "s2Gv2ProPlus.pth").write_text("stub", encoding="utf-8")
            (root / "GPT_SoVITS" / "pretrained_models" / "s1v3.ckpt").write_text("stub", encoding="utf-8")
            (root / "weight.json").write_text(
                json.dumps(
                    {
                        "GPT": {"v2": "GPT_SoVITS/pretrained_models/s1v3.ckpt"},
                        "SoVITS": {"v2": "SoVITS_weights_v2ProPlus/missing.pth"},
                    }
                ),
                encoding="utf-8",
            )

            checks = startup_check.check_weight_json(root)

        missing = [check for check in checks if not check.ok]
        self.assertEqual(1, len(missing))
        self.assertEqual("weight.json SoVITS v2", missing[0].name)
        self.assertIn("不存在", missing[0].message)
        self.assertIn("s2Gv2ProPlus.pth", missing[0].message)

    def test_report_is_not_startable_when_required_paths_are_missing(self):
        from tools import startup_check

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "weight.json").write_text("{}", encoding="utf-8")
            report = startup_check.build_report(root, check_cuda=False, check_ports=False)

        self.assertFalse(report.ok)
        rendered = report.render()
        self.assertIn("不可启动", rendered)
        self.assertIn("缺失", rendered)

    def test_build_report_runs_cuda_checker_without_name_collision(self):
        from tools import startup_check

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "py312").mkdir()
            (root / "py312" / "python.exe").write_text("stub", encoding="utf-8")
            pretrained = root / "GPT_SoVITS" / "pretrained_models"
            (pretrained / "chinese-roberta-wwm-ext-large").mkdir(parents=True)
            (pretrained / "chinese-hubert-base").mkdir()
            (pretrained / "s1v3.ckpt").write_text("stub", encoding="utf-8")
            (pretrained / "v2Pro").mkdir()
            (pretrained / "v2Pro" / "s2Gv2ProPlus.pth").write_text("stub", encoding="utf-8")
            config_dir = root / "GPT_SoVITS" / "configs"
            config_dir.mkdir()
            (root / "api_v2.py").write_text("stub", encoding="utf-8")
            (config_dir / "tts_infer.yaml").write_text(
                """
custom:
  t2s_weights_path: GPT_SoVITS/pretrained_models/s1v3.ckpt
  vits_weights_path: GPT_SoVITS/pretrained_models/v2Pro/s2Gv2ProPlus.pth
  bert_base_path: GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large
  cnhuhbert_base_path: GPT_SoVITS/pretrained_models/chinese-hubert-base
""",
                encoding="utf-8",
            )

            original = startup_check.check_cuda_status
            startup_check.check_cuda_status = lambda: startup_check.CheckResult("CUDA", True, "stubbed")
            try:
                report = startup_check.build_report(root, mode="api", check_cuda=True, check_ports=False)
            finally:
                startup_check.check_cuda_status = original

        self.assertTrue(any(check.name == "CUDA" for check in report.checks))


if __name__ == "__main__":
    unittest.main()
