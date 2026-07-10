import os
from pathlib import Path
from shutil import copyfile

from tools.list_metadata import format_list_line, parse_list_line


PREFERRED_ASR_LIST_NAMES = ("音频修改.list", "语音.list", "音频.list")


def iter_asr_list_files(asr_dir):
    asr_dir = Path(asr_dir)
    if not asr_dir.exists() or not asr_dir.is_dir():
        return []

    files = []
    seen = set()
    for name in PREFERRED_ASR_LIST_NAMES:
        path = asr_dir / name
        if path.exists() and path.is_file():
            files.append(path)
            seen.add(path.name)

    for path in sorted(asr_dir.glob("*.list"), key=lambda item: item.name):
        if path.name not in seen:
            files.append(path)
            seen.add(path.name)
    return files


def _clean_field(value):
    return str(value or "").strip()


def resolve_reference_character(
    current_character="",
    metadata_character="",
    experiment_character="",
    speaker_name="",
):
    for value in (current_character, metadata_character, experiment_character, speaker_name):
        value = _clean_field(value)
        if value and value != "全部":
            return value
    return ""


def _merge_metadata(existing, incoming):
    if not existing:
        return incoming
    merged = dict(existing)
    for key, value in incoming.items():
        if not merged.get(key) and value:
            merged[key] = value
    return merged


def parse_asr_list_line(line):
    item = parse_list_line(line)
    if item is None:
        return None

    wav_path = _clean_field(item.wav_path).strip("\"'")
    name = os.path.basename(wav_path)
    if not name:
        return None

    return {
        "name": name,
        "wav_path": wav_path,
        "speaker_name": item.speaker_name,
        "lang": item.language,
        "text": item.text,
        "emotion": item.emotion,
        "remark": item.remark,
    }


def read_asr_metadata_from_dir(asr_dir):
    metadata = {}
    for list_path in iter_asr_list_files(asr_dir):
        try:
            with open(list_path, "r", encoding="utf-8", errors="ignore") as fp:
                for line in fp.read().splitlines():
                    item = parse_asr_list_line(line)
                    if not item:
                        continue
                    name = item.pop("name")
                    metadata[name] = _merge_metadata(metadata.get(name), item)
        except Exception:
            continue
    return metadata


def read_asr_metadata_map(root, exp):
    return read_asr_metadata_from_dir(Path(root) / "output" / "asr_opt" / str(exp))


def update_asr_list_metadata(list_path, audio_name, text=None, emotion=None, remark=None):
    list_path = Path(list_path)
    if not list_path.exists():
        return False

    lines = list_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    updated_lines = []
    changed = False
    target_name = os.path.basename(str(audio_name or ""))

    for line in lines:
        item = parse_list_line(line)
        if item is None:
            updated_lines.append(line)
            continue

        if os.path.basename(item.wav_path.strip("\"'")) == target_name:
            new_text = str(text) if text not in [None, ""] else item.text
            new_emotion = str(emotion) if emotion not in [None, ""] else item.emotion
            new_remark = str(remark) if remark not in [None, ""] else item.remark
            item = item.__class__(
                wav_path=item.wav_path,
                speaker_name=item.speaker_name,
                language=item.language,
                text=new_text,
                emotion=new_emotion,
                remark=new_remark,
            )
            changed = True
        updated_lines.append(format_list_line(item))

    if not changed:
        return False

    backup_path = list_path.with_suffix(list_path.suffix + ".bak")
    copyfile(list_path, backup_path)
    list_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
    return True
