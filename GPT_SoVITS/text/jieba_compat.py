"""Prefer jieba-fast where available, with a pure-Python Windows fallback."""

try:
    import jieba_fast as jieba
    import jieba_fast.posseg as psg
except ImportError:
    import jieba
    import jieba.posseg as psg


__all__ = ["jieba", "psg"]
