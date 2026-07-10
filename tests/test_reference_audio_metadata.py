import tempfile
import unittest
from pathlib import Path


class ReferenceAudioMetadataTests(unittest.TestCase):
    def test_reads_emotion_from_non_preferred_list_filename(self):
        from tools.reference_audio_metadata import read_asr_metadata_map

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asr_dir = root / "output" / "asr_opt" / "胶布TTS新-20260611"
            asr_dir.mkdir(parents=True)
            (asr_dir / "胶布TTS新.list").write_text(
                r"\\server\share\胶布TTS新_01.wav|胶布TTS新-华|ZH|不好！地板开始裂开了！再不跑我们全都要掉下去！ |惊恐|"
                + "\n",
                encoding="utf-8",
            )

            metadata = read_asr_metadata_map(root, "胶布TTS新-20260611")

        self.assertIn("胶布TTS新_01.wav", metadata)
        self.assertEqual(metadata["胶布TTS新_01.wav"]["speaker_name"], "胶布TTS新-华")
        self.assertEqual(metadata["胶布TTS新_01.wav"]["text"], "不好！地板开始裂开了！再不跑我们全都要掉下去！")
        self.assertEqual(metadata["胶布TTS新_01.wav"]["emotion"], "惊恐")

    def test_preferred_list_files_are_read_before_other_lists(self):
        from tools.reference_audio_metadata import iter_asr_list_files

        with tempfile.TemporaryDirectory() as tmp:
            asr_dir = Path(tmp)
            for name in ["胶布TTS新.list", "语音.list", "音频修改.list"]:
                (asr_dir / name).write_text("", encoding="utf-8")

            names = [path.name for path in iter_asr_list_files(asr_dir)]

        self.assertEqual(names, ["音频修改.list", "语音.list", "胶布TTS新.list"])

    def test_experiment_character_overrides_stale_list_speaker_name(self):
        from tools.reference_audio_metadata import resolve_reference_character

        character = resolve_reference_character(
            current_character="",
            metadata_character="",
            experiment_character="白泽TTS新",
            speaker_name="胶布TTS新-华",
        )

        self.assertEqual(character, "白泽TTS新")


if __name__ == "__main__":
    unittest.main()
