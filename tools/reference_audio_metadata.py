import os
from pathlib import Path


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
    if "|" not in line:
        return None
    parts = line.rstrip("\n").split("|")
    if len(parts) < 4:
        return None

    wav_path = _clean_field(parts[0]).strip("\"'")
    name = os.path.basename(wav_path)
    if not name:
        return None

    return {
        "name": name,
        "wav_path": wav_path,
        "speaker_name": _clean_field(parts[1]),
        "lang": _clean_field(parts[2]),
        "text": _clean_field(parts[3]),
        "emotion": _clean_field(parts[4]) if len(parts) >= 5 else "",
        "remark": _clean_field(parts[5]) if len(parts) >= 6 else "",
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
