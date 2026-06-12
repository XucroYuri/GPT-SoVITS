import os


def check_fw_local_models():
    """Return Faster Whisper choices, marking locally available models."""
    model_size_list = [
        "tiny",
        "tiny.en",
        "base",
        "base.en",
        "small",
        "small.en",
        "medium",
        "medium.en",
        "large",
        "large-v1",
        "large-v2",
        "large-v3",
        "large-v3-turbo",
    ]
    for i, size in enumerate(model_size_list):
        if os.path.exists(f"tools/asr/models/faster-whisper-{size}"):
            model_size_list[i] = size + "-local"
    return model_size_list


asr_dict = {
    "Fun-ASR-Nano (31语种+方言, 推荐)": {"lang": ["zh", "en", "ja", "ko", "yue", "auto"], "size": ["large"], "path": "funasr_asr.py", "precision": ["float32"]},
    "SenseVoice (极速, 5语种)": {"lang": ["zh", "en", "ja", "ko", "yue", "auto"], "size": ["large"], "path": "funasr_asr.py", "precision": ["float32"]},
    "达摩 ASR (中文经典)": {"lang": ["zh", "yue"], "size": ["large"], "path": "funasr_asr.py", "precision": ["float32"]},
    "Faster Whisper (多语种)": {
        "lang": ["auto", "zh", "en", "ja", "ko", "yue"],
        "size": check_fw_local_models(),
        "path": "fasterwhisper_asr.py",
        "precision": ["float32", "float16", "int8"],
    },
}
