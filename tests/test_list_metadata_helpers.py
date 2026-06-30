import tempfile
import unittest
from pathlib import Path


class ListMetadataHelpersTests(unittest.TestCase):
    def test_parses_four_column_training_list_and_ignores_metadata_for_training(self):
        from tools.list_metadata import parse_list_line

        item = parse_list_line(r"C:\voice\a.wav|角色A|ZH|你好")

        self.assertEqual(item.wav_path, r"C:\voice\a.wav")
        self.assertEqual(item.speaker_name, "角色A")
        self.assertEqual(item.language, "ZH")
        self.assertEqual(item.text, "你好")
        self.assertEqual(item.emotion, "")
        self.assertEqual(item.remark, "")
        self.assertEqual(item.training_fields, [r"C:\voice\a.wav", "角色A", "ZH", "你好"])

    def test_parses_six_column_metadata_list_without_feeding_extra_fields_to_training(self):
        from tools.list_metadata import parse_list_line

        item = parse_list_line(r"C:\voice\a.wav|角色A|ZH|你好|开心|第一轮精选")

        self.assertEqual(item.emotion, "开心")
        self.assertEqual(item.remark, "第一轮精选")
        self.assertEqual(item.training_fields, [r"C:\voice\a.wav", "角色A", "ZH", "你好"])

    def test_formats_as_six_column_metadata_line(self):
        from tools.list_metadata import ListLine, format_list_line

        line = format_list_line(
            ListLine(
                wav_path="a.wav",
                speaker_name="角色A",
                language="ZH",
                text="你好",
                emotion="开心",
                remark="第一轮精选",
            )
        )

        self.assertEqual(line, "a.wav|角色A|ZH|你好|开心|第一轮精选")

    def test_updates_asr_list_metadata_and_creates_backup(self):
        from tools.reference_audio_metadata import update_asr_list_metadata

        with tempfile.TemporaryDirectory() as tmp:
            list_path = Path(tmp) / "语音.list"
            list_path.write_text(
                "a.wav|旧角色|ZH|旧文本\n"
                "b.wav|旧角色|ZH|保留文本|平静|保留备注\n",
                encoding="utf-8",
            )

            changed = update_asr_list_metadata(
                list_path,
                audio_name="a.wav",
                text="新文本",
                emotion="开心",
                remark="精选",
            )

            self.assertTrue(changed)
            self.assertEqual(
                list_path.read_text(encoding="utf-8").splitlines(),
                [
                    "a.wav|旧角色|ZH|新文本|开心|精选",
                    "b.wav|旧角色|ZH|保留文本|平静|保留备注",
                ],
            )
            self.assertEqual(
                list_path.with_suffix(".list.bak").read_text(encoding="utf-8").splitlines(),
                [
                    "a.wav|旧角色|ZH|旧文本",
                    "b.wav|旧角色|ZH|保留文本|平静|保留备注",
                ],
            )


if __name__ == "__main__":
    unittest.main()
