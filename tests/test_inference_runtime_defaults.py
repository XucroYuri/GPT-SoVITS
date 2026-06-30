import unittest
from pathlib import Path


class InferenceRuntimeDefaultsTests(unittest.TestCase):
    def test_shared_runtime_defaults_are_declared_once(self):
        from tools.inference_model_defaults import DEFAULT_TEXT_SPLIT_METHOD, DEFAULT_TOP_K

        self.assertEqual(DEFAULT_TOP_K, 15)
        self.assertEqual(DEFAULT_TEXT_SPLIT_METHOD, "cut5")

    def test_api_and_tts_use_shared_defaults(self):
        root = Path(__file__).resolve().parents[1]
        api_v2 = (root / "api_v2.py").read_text(encoding="utf-8")
        tts = (root / "GPT_SoVITS" / "TTS_infer_pack" / "TTS.py").read_text(encoding="utf-8")

        self.assertIn("DEFAULT_TOP_K", api_v2)
        self.assertIn("DEFAULT_TEXT_SPLIT_METHOD", api_v2)
        self.assertIn("DEFAULT_TOP_K", tts)
        self.assertIn("DEFAULT_TEXT_SPLIT_METHOD", tts)
        self.assertNotIn('text_split_method: str = "cut0"', api_v2)
        self.assertNotIn('text_split_method: str = "cut0"', tts)

    def test_portable_mode_is_entrypoint_scoped(self):
        root = Path(__file__).resolve().parents[1]
        webui = (root / "webui.py").read_text(encoding="utf-8")
        train_script = (root / "启动_训练WebUI.bat").read_text(encoding="utf-8")
        infer_script = (root / "启动_推理WebUI.bat").read_text(encoding="utf-8")
        api_script = (root / "启动_API服务.bat").read_text(encoding="utf-8")

        self.assertIn("GPT_SOVITS_PORTABLE_MODE", webui)
        self.assertNotIn("os.environ['TRANSFORMERS_OFFLINE'] = '1'", webui)
        self.assertIn('set "GPT_SOVITS_PORTABLE_MODE=1"', train_script)
        self.assertIn('set "GPT_SOVITS_PORTABLE_MODE=1"', infer_script)
        self.assertIn('set "GPT_SOVITS_PORTABLE_MODE=1"', api_script)


if __name__ == "__main__":
    unittest.main()
