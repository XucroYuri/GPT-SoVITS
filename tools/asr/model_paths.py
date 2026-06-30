import os
from pathlib import Path


def asr_model_root(project_root=None):
    override = os.environ.get("GPT_SOVITS_ASR_MODELS_DIR")
    if override:
        return Path(override).expanduser()
    root = Path(project_root) if project_root is not None else Path.cwd()
    return root / "tools" / "asr" / "models"


def local_model_or_repo(root, local_name, repo_name):
    local_path = Path(root) / local_name
    return str(local_path) if local_path.exists() else repo_name
