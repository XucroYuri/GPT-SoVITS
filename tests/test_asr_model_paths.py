import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class AsrModelPathsTests(unittest.TestCase):
    def test_asr_model_root_defaults_to_project_local_models(self):
        from tools.asr.model_paths import asr_model_root

        with mock.patch.dict(os.environ, {}, clear=True):
            root = asr_model_root(project_root=Path("J:/repo"))

        self.assertEqual(root, Path("J:/repo") / "tools" / "asr" / "models")

    def test_asr_model_root_honors_environment_override(self):
        from tools.asr.model_paths import asr_model_root

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"GPT_SOVITS_ASR_MODELS_DIR": tmp}, clear=True):
                root = asr_model_root(project_root=Path("J:/repo"))

            self.assertEqual(root, Path(tmp))

    def test_local_model_path_prefers_existing_directory(self):
        from tools.asr.model_paths import local_model_or_repo

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local = root / "speech_model"
            local.mkdir()

            self.assertEqual(local_model_or_repo(root, "speech_model", "iic/speech_model"), str(local))
            self.assertEqual(local_model_or_repo(root, "missing_model", "iic/missing_model"), "iic/missing_model")


if __name__ == "__main__":
    unittest.main()
