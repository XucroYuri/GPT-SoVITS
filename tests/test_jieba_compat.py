from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPAT_MODULE = REPO_ROOT / "GPT_SoVITS" / "text" / "jieba_compat.py"
JAPANESE_MODULE = REPO_ROOT / "GPT_SoVITS" / "text" / "japanese.py"


def _load_compat(module_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, COMPAT_MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_jieba_compat_falls_back_to_pure_python_package() -> None:
    slow = ModuleType("jieba")
    slow_posseg = ModuleType("jieba.posseg")
    slow.posseg = slow_posseg

    with mock.patch.dict(
        sys.modules,
        {"jieba_fast": None, "jieba": slow, "jieba.posseg": slow_posseg},
        clear=False,
    ):
        compat = _load_compat("jieba_compat_slow_test")

    assert compat.jieba is slow
    assert compat.psg is slow_posseg


def test_jieba_compat_prefers_fast_package_when_available() -> None:
    fast = ModuleType("jieba_fast")
    fast_posseg = ModuleType("jieba_fast.posseg")
    fast.posseg = fast_posseg
    slow = ModuleType("jieba")
    slow_posseg = ModuleType("jieba.posseg")
    slow.posseg = slow_posseg

    with mock.patch.dict(
        sys.modules,
        {
            "jieba_fast": fast,
            "jieba_fast.posseg": fast_posseg,
            "jieba": slow,
            "jieba.posseg": slow_posseg,
        },
        clear=False,
    ):
        compat = _load_compat("jieba_compat_fast_test")

    assert compat.jieba is fast
    assert compat.psg is fast_posseg


def test_japanese_frontend_tolerates_missing_optional_user_dictionary_api() -> None:
    frontend = ModuleType("pyopenjtalk")
    frontend.OPEN_JTALK_DICT_DIR = str(REPO_ROOT).encode("utf-8")
    frontend.g2p = lambda text: "k o N"
    frontend.run_frontend = lambda text: []
    frontend.make_label = lambda features: []

    spec = importlib.util.spec_from_file_location("japanese_openjtalk_compat_test", JAPANESE_MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"pyopenjtalk": frontend}, clear=False), mock.patch.object(
        sys, "path", [str(REPO_ROOT / "GPT_SoVITS"), *sys.path]
    ):
        spec.loader.exec_module(module)

    assert module.pyopenjtalk is frontend
    assert frontend.g2p("こんにちは") == "k o N"
