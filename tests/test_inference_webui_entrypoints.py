import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def function_source(path: Path, function_name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"{function_name} not found in {path}")


class InferenceWebuiEntrypointTests(unittest.TestCase):
    def test_main_launcher_uses_custom_inference_ui_for_both_modes(self):
        launcher = function_source(ROOT / "webui.py", "change_tts_inference")

        self.assertIn("GPT_SoVITS/inference_webui.py", launcher)
        self.assertNotIn("GPT_SoVITS/inference_webui_fast.py", launcher)

    def test_fast_entrypoint_delegates_to_custom_inference_ui(self):
        fast_entrypoint = (ROOT / "GPT_SoVITS/inference_webui_fast.py").read_text(encoding="utf-8")

        self.assertIn("runpy.run_path", fast_entrypoint)
        self.assertIn("inference_webui.py", fast_entrypoint)
        self.assertNotIn("with gr.Blocks", fast_entrypoint)


if __name__ == "__main__":
    unittest.main()
