from dataclasses import dataclass


@dataclass(frozen=True)
class ListLine:
    wav_path: str
    speaker_name: str
    language: str
    text: str
    emotion: str = ""
    remark: str = ""

    @property
    def training_fields(self):
        return [self.wav_path, self.speaker_name, self.language, self.text]


def _clean(value):
    return str(value or "").strip()


def parse_list_line(line):
    parts = str(line or "").rstrip("\r\n").split("|")
    if len(parts) < 4:
        return None
    return ListLine(
        wav_path=_clean(parts[0]),
        speaker_name=_clean(parts[1]),
        language=_clean(parts[2]),
        text=_clean(parts[3]),
        emotion=_clean(parts[4]) if len(parts) >= 5 else "",
        remark=_clean(parts[5]) if len(parts) >= 6 else "",
    )


def format_list_line(item):
    return "|".join(
        [
            str(item.wav_path or ""),
            str(item.speaker_name or ""),
            str(item.language or ""),
            str(item.text or ""),
            str(item.emotion or ""),
            str(item.remark or ""),
        ]
    )
