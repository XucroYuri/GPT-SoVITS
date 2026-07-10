import argparse
import json
import os
import socket
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None


PRETRAINED_HINTS = {
    "GPT": [
        "GPT_SoVITS/pretrained_models/s1v3.ckpt",
        "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt",
        "GPT_SoVITS/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt",
    ],
    "SoVITS": [
        "GPT_SoVITS/pretrained_models/v2Pro/s2Gv2ProPlus.pth",
        "GPT_SoVITS/pretrained_models/v2Pro/s2Gv2Pro.pth",
        "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth",
        "GPT_SoVITS/pretrained_models/s2Gv3.pth",
        "GPT_SoVITS/pretrained_models/gsv-v4-pretrained/s2Gv4.pth",
        "GPT_SoVITS/pretrained_models/s2G488k.pth",
    ],
}

MODE_PORTS = {"train": 9874, "infer-webui": 9872, "api": 9880}


@dataclass
class CheckResult:
    name: str
    ok: bool
    message: str
    level: str = "ERROR"

    @property
    def blocks_startup(self):
        return not self.ok and self.level.upper() == "ERROR"


@dataclass
class StartupReport:
    mode: str
    checks: list

    @property
    def ok(self):
        return not any(check.blocks_startup for check in self.checks)

    def render(self):
        status = "可启动" if self.ok else "不可启动"
        lines = [f"启动预检({self.mode}): {status}"]
        for check in self.checks:
            mark = "OK" if check.ok else check.level.upper()
            lines.append(f"[{mark}] {check.name}: {check.message}")
        return "\n".join(lines)


def _full_path(root, path_value):
    path = Path(str(path_value))
    return path if path.is_absolute() else Path(root) / path


def _existing_hints(root, kind, limit=6):
    root = Path(root)
    hints = []
    for item in PRETRAINED_HINTS.get(kind, []):
        if _full_path(root, item).exists():
            hints.append(item)
    patterns = ["GPT_weights*/*.ckpt", "GPT_SoVITS/pretrained_models/**/*.ckpt"] if kind == "GPT" else [
        "SoVITS_weights*/*.pth",
        "GPT_SoVITS/pretrained_models/**/*.pth",
    ]
    for pattern in patterns:
        for path in root.glob(pattern):
            rel = path.relative_to(root).as_posix()
            if rel not in hints:
                hints.append(rel)
            if len(hints) >= limit:
                return hints
    return hints[:limit]


def _format_hints(root, kind):
    hints = _existing_hints(root, kind)
    if not hints:
        return "未发现可用预训练权重"
    return "可用预训练/本地权重: " + ", ".join(hints)


def require_existing_weight_path(label, path_value, root=None, kind="GPT", name_map=None):
    root = Path(root or os.getcwd())
    if path_value is None or str(path_value).strip() == "":
        raise FileNotFoundError(f"{label} 为空。{_format_hints(root, kind)}")
    if name_map and path_value in name_map:
        path_value = name_map[path_value]
    if "!" in str(path_value) or "！" in str(path_value):
        return path_value

    full = _full_path(root, path_value)
    if not full.exists():
        raise FileNotFoundError(f"{label} 不存在: {path_value}。{_format_hints(root, kind)}")
    return str(path_value)


def _check_path(root, name, path_value, kind=None, level="ERROR"):
    if not path_value:
        return CheckResult(name, False, "路径为空", level)
    full = _full_path(root, path_value)
    if full.exists():
        return CheckResult(name, True, str(path_value), "OK")
    hint = f"。{_format_hints(root, kind)}" if kind else ""
    return CheckResult(name, False, f"缺失/不存在: {path_value}{hint}", level)


def check_common_paths(root, mode="all"):
    root = Path(root)
    checks = [
        _check_path(root, "内置 Python", "py312/python.exe"),
        _check_path(root, "中文 BERT", "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large"),
        _check_path(root, "CNHuBERT", "GPT_SoVITS/pretrained_models/chinese-hubert-base"),
    ]
    if mode in {"all", "train"}:
        checks.append(_check_path(root, "训练入口", "webui.py"))
    if mode in {"all", "infer-webui"}:
        checks.append(_check_path(root, "推理 WebUI 入口", "GPT_SoVITS/inference_webui.py"))
    if mode in {"all", "api"}:
        checks.append(_check_path(root, "API 入口", "api_v2.py"))
        checks.append(_check_path(root, "API 推理配置", "GPT_SoVITS/configs/tts_infer.yaml"))
    return checks


def check_weight_json(root, level="ERROR"):
    root = Path(root)
    weight_file = root / "weight.json"
    if not weight_file.exists():
        return [CheckResult("weight.json", False, "缺失 weight.json", level)]
    try:
        data = json.loads(weight_file.read_text(encoding="utf-8"))
    except Exception as exc:
        return [CheckResult("weight.json", False, f"无法解析: {exc}", level)]

    checks = []
    for kind in ("GPT", "SoVITS"):
        values = data.get(kind, {})
        if not isinstance(values, dict):
            checks.append(CheckResult(f"weight.json {kind}", False, "格式应为对象", level))
            continue
        for version, path_value in values.items():
            checks.append(_check_path(root, f"weight.json {kind} {version}", path_value, kind, level))
    return checks or [CheckResult("weight.json", True, "未配置自定义权重，将使用入口默认值", "OK")]


def check_tts_yaml(root, level="ERROR"):
    root = Path(root)
    config_file = root / "GPT_SoVITS" / "configs" / "tts_infer.yaml"
    if not config_file.exists():
        return [CheckResult("tts_infer.yaml", False, "缺失 API 推理配置", level)]
    if yaml is None:
        return [CheckResult("tts_infer.yaml", False, "无法导入 yaml 模块", level)]
    try:
        data = yaml.load(config_file.read_text(encoding="utf-8"), Loader=yaml.FullLoader)
    except Exception as exc:
        return [CheckResult("tts_infer.yaml", False, f"无法解析: {exc}", level)]
    custom = (data or {}).get("custom", {})
    checks = [
        _check_path(root, "tts_infer GPT权重", custom.get("t2s_weights_path"), "GPT", level),
        _check_path(root, "tts_infer SoVITS权重", custom.get("vits_weights_path"), "SoVITS", level),
        _check_path(root, "tts_infer BERT", custom.get("bert_base_path"), None, level),
        _check_path(root, "tts_infer CNHuBERT", custom.get("cnhuhbert_base_path"), None, level),
    ]
    return checks


def check_port(port, level="ERROR"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        used = sock.connect_ex(("127.0.0.1", int(port))) == 0
    if used:
        return CheckResult(f"端口 {port}", False, "已被占用，请先关闭对应服务或换端口", level)
    return CheckResult(f"端口 {port}", True, "未占用", "OK")


def check_cuda_status():
    try:
        from tools.startup_bootstrap import apply_startup_patches

        apply_startup_patches(logger=None)
        import torch

        available = torch.cuda.is_available()
        count = torch.cuda.device_count() if available else 0
        message = f"torch {torch.__version__}, CUDA {'可用' if available else '不可用'}, GPU数量 {count}"
        return CheckResult("CUDA", True, message, "OK" if available else "WARN")
    except Exception as exc:
        return CheckResult("CUDA", True, f"无法检测 CUDA: {exc}", "WARN")


def build_report(root=None, mode="all", check_cuda=True, check_ports=True):
    root = Path(root or os.getcwd())
    checks = check_common_paths(root, mode)
    if mode in {"all", "infer-webui"}:
        checks.extend(check_weight_json(root, "ERROR"))
    elif mode == "train":
        checks.extend(check_weight_json(root, "WARN"))
    if mode in {"all", "api"}:
        checks.extend(check_tts_yaml(root, "ERROR"))
    if check_ports:
        if mode == "all":
            for port in MODE_PORTS.values():
                checks.append(check_port(port, "WARN"))
        elif mode in MODE_PORTS:
            checks.append(check_port(MODE_PORTS[mode], "ERROR"))
    if check_cuda:
        checks.append(check_cuda_status())
    return StartupReport(mode, checks)


def main(argv=None):
    parser = argparse.ArgumentParser(description="GPT-SoVITS 启动预检")
    parser.add_argument("--mode", choices=["all", "train", "infer-webui", "api"], default="all")
    parser.add_argument("--root", default=os.getcwd())
    parser.add_argument("--skip-cuda", action="store_true")
    parser.add_argument("--skip-ports", action="store_true")
    args = parser.parse_args(argv)

    report = build_report(args.root, args.mode, check_cuda=not args.skip_cuda, check_ports=not args.skip_ports)
    print(report.render())
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
