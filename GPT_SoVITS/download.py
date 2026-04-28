import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

now_dir = os.getcwd()
sys.path.insert(0, now_dir)
from model_store import apply_project_runtime_env, pretrained_model_path
apply_project_runtime_env()
from text.g2pw import G2PWPinyin

g2pw = G2PWPinyin(
    model_dir="GPT_SoVITS/text/G2PWModel",
    model_source=str(pretrained_model_path("chinese-roberta-wwm-ext-large")),
    v_to_u=False,
    neutral_tone_with_five=True,
)
