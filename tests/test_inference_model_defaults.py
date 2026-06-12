import unittest
import ast
from pathlib import Path


class InferenceModelDefaultsTests(unittest.TestCase):
    def test_inference_webui_does_not_call_i18n_before_initialization(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "GPT_SoVITS" / "inference_webui.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        init_line = next(
            node.lineno
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "i18n" for target in node.targets)
        )

        class TopLevelI18nCalls(ast.NodeVisitor):
            def __init__(self):
                self.calls = []
                self.depth = 0

            def visit_FunctionDef(self, node):
                return

            def visit_ClassDef(self, node):
                return

            def visit_Call(self, node):
                if (
                    self.depth == 0
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "i18n"
                    and node.lineno < init_line
                ):
                    self.calls.append(node.lineno)
                self.generic_visit(node)

        visitor = TopLevelI18nCalls()
        visitor.visit(tree)
        self.assertEqual(visitor.calls, [])

    def test_pretrained_paths_are_displayed_as_default_dropdown_labels(self):
        from tools.inference_model_defaults import resolve_weight_selection

        selection = resolve_weight_selection(
            env_value=None,
            stored_value="GPT_SoVITS/pretrained_models/s1v3.ckpt",
            fallback_choice="GPT_weights_v2ProPlus/custom.ckpt",
            default_label="不训练直接推v3底模！",
            name_map={
                "不训练直接推v2底模！": "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1.ckpt",
                "不训练直接推v3底模！": "GPT_SoVITS/pretrained_models/s1v3.ckpt",
            },
        )

        self.assertEqual(selection.display_value, "不训练直接推v3底模！")
        self.assertEqual(selection.resolved_path, "GPT_SoVITS/pretrained_models/s1v3.ckpt")

    def test_missing_stored_value_prefers_packaged_default_label(self):
        from tools.inference_model_defaults import resolve_weight_selection

        selection = resolve_weight_selection(
            env_value="",
            stored_value=None,
            fallback_choice="SoVITS_weights_v2ProPlus/custom.pth",
            default_label="不训练直接推v2ProPlus底模！",
            name_map={
                "不训练直接推v2Pro底模！": "GPT_SoVITS/pretrained_models/v2Pro/s2Gv2Pro.pth",
                "不训练直接推v2ProPlus底模！": "GPT_SoVITS/pretrained_models/v2Pro/s2Gv2ProPlus.pth",
            },
        )

        self.assertEqual(selection.display_value, "不训练直接推v2ProPlus底模！")
        self.assertEqual(selection.resolved_path, "GPT_SoVITS/pretrained_models/v2Pro/s2Gv2ProPlus.pth")

    def test_trained_model_path_is_preserved(self):
        from tools.inference_model_defaults import resolve_weight_selection

        selection = resolve_weight_selection(
            env_value=None,
            stored_value="GPT_weights_v2ProPlus/白泽TTS新-20260611-e50.ckpt",
            fallback_choice="不训练直接推v3底模！",
            default_label="不训练直接推v3底模！",
            name_map={"不训练直接推v3底模！": "GPT_SoVITS/pretrained_models/s1v3.ckpt"},
        )

        self.assertEqual(selection.display_value, "GPT_weights_v2ProPlus/白泽TTS新-20260611-e50.ckpt")
        self.assertEqual(selection.resolved_path, "GPT_weights_v2ProPlus/白泽TTS新-20260611-e50.ckpt")


if __name__ == "__main__":
    unittest.main()
