import tempfile
import unittest
from pathlib import Path


class SubfixListMetadataTests(unittest.TestCase):
    def test_set_global_resets_previous_list_data(self):
        from tools import subfix_webui

        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.list"
            second = Path(tmp) / "second.list"
            first.write_text("a.wav|角色A|ZH|第一句\n", encoding="utf-8")
            second.write_text("b.wav|角色B|ZH|第二句|难过|精选\n", encoding="utf-8")

            subfix_webui.set_global("None", str(first), "text", "wav_path", 1)
            subfix_webui.set_global("None", str(second), "text", "wav_path", 1)

            self.assertEqual(len(subfix_webui.g_data_json), 1)
            self.assertEqual(subfix_webui.g_data_json[0]["wav_path"], "b.wav")
            self.assertEqual(subfix_webui.g_data_json[0]["emotion"], "难过")
            self.assertEqual(subfix_webui.g_data_json[0]["remark"], "精选")

    def test_four_column_list_saves_back_as_six_column_metadata_list(self):
        from tools import subfix_webui

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "voice.list"
            source.write_text("a.wav|角色A|ZH|旧文本\n", encoding="utf-8")

            subfix_webui.set_global("None", str(source), "text", "wav_path", 1)
            subfix_webui.b_submit_change("新文本", "开心", "精选")

            self.assertEqual(source.read_text(encoding="utf-8").strip(), "a.wav|角色A|ZH|新文本 |开心|精选")


if __name__ == "__main__":
    unittest.main()
