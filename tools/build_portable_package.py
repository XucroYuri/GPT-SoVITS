import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PACKAGE_PREFIX = "GPT-SoVITS-v2ProPlus-Portable"
PRETRAINED_WEIGHT_CONFIG = {
    "GPT": {"v2": "GPT_SoVITS/pretrained_models/s1v3.ckpt"},
    "SoVITS": {"v2": "GPT_SoVITS/pretrained_models/v2Pro/s2Gv2ProPlus.pth"},
}

WEIGHT_DIRS = [
    "GPT_weights",
    "GPT_weights_v2",
    "GPT_weights_v2Pro",
    "GPT_weights_v2ProPlus",
    "GPT_weights_v3",
    "GPT_weights_v4",
    "SoVITS_weights",
    "SoVITS_weights_v2",
    "SoVITS_weights_v2Pro",
    "SoVITS_weights_v2ProPlus",
    "SoVITS_weights_v3",
    "SoVITS_weights_v4",
]

RUNTIME_EMPTY_DIRS = [
    "logs/startup",
    "tmp",
    "TEMP",
    "tf_download",
    "output/asr_opt",
    "output/slicer_opt",
    *WEIGHT_DIRS,
]

ROOT_LEGACY_FILES = {
    "app.py",
    "api.py",
    "character_map.json",
    "go-webui.ps1",
    "开始训练.bat",
    "运行_统一推理WebUI.bat",
    "运行_自动开启接口服务.bat",
    "打包_绿色版.bat",
}

ROOT_EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "logs",
    "output",
    "temp",
    "tests",
    "tmp",
    "__pycache__",
}

NESTED_EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}


@dataclass
class PackageResult:
    staging_dir: Path
    zip_path: Path | None
    zip_error: str | None = None


def _normalized_parts(rel_path):
    normalized = str(rel_path).replace("\\", "/").strip("/")
    if normalized in {"", "."}:
        return []
    return [part for part in normalized.split("/") if part and part != "."]


def should_exclude(rel_path):
    parts = _normalized_parts(rel_path)
    if not parts:
        return False

    lower_parts = [part.lower() for part in parts]
    root = lower_parts[0]
    name = parts[-1]
    lower_name = lower_parts[-1]

    if any(part in NESTED_EXCLUDED_DIRS for part in lower_parts):
        return True
    if root in ROOT_EXCLUDED_DIRS:
        return True
    if root.startswith("gpt_weights") or root.startswith("sovits_weights"):
        return True
    if len(parts) == 1 and name in ROOT_LEGACY_FILES:
        return True
    if lower_name.endswith((".pyc", ".pyo")):
        return True
    return False


def _write_text_crlf(path, text, encoding="utf-8"):
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalized.replace("\n", "\r\n"), encoding=encoding)


def _ensure_inside(child, parent):
    child = Path(child).resolve()
    parent = Path(parent).resolve()
    if child == parent or parent not in child.parents:
        raise ValueError(f"refusing to operate outside staging parent: {child}")
    return child


def _remove_if_exists(path, allowed_parent):
    path = _ensure_inside(path, allowed_parent)
    if path.exists():
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            pass


def _copy_directory_with_robocopy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "robocopy",
        str(source),
        str(target),
        "/E",
        "/R:2",
        "/W:1",
        "/NP",
        "/NFL",
        "/NDL",
        "/NJH",
        "/NJS",
        "/XD",
        *NESTED_EXCLUDED_DIRS,
        "/XF",
        "*.pyc",
        "*.pyo",
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode >= 8:
        raise RuntimeError(
            f"robocopy failed for {source.name} with code {completed.returncode}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )


def copy_project_to_staging(source_root, staging_dir):
    source_root = Path(source_root).resolve()
    staging_dir = Path(staging_dir).resolve()
    staging_dir.mkdir(parents=True, exist_ok=True)

    for item in source_root.iterdir():
        rel_name = item.name
        if should_exclude(rel_name):
            continue
        target = staging_dir / rel_name
        if item.is_dir():
            _copy_directory_with_robocopy(item, target)
        elif item.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def write_weight_json(staging_dir):
    weight_path = Path(staging_dir) / "weight.json"
    weight_path.write_text(
        json.dumps(PRETRAINED_WEIGHT_CONFIG, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_start_menu(staging_dir):
    menu = """@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

:menu
cls
echo GPT-SoVITS 绿色版启动菜单
echo.
echo 1 推理WebUI(9872)
echo 2 训练WebUI(9874)
echo 3 API服务(9880/docs)
echo 0 退出
echo.
set /p choice=请选择启动项:

if "%choice%"=="1" (
    call "启动_推理WebUI.bat"
    goto menu
)
if "%choice%"=="2" (
    call "启动_训练WebUI.bat"
    goto menu
)
if "%choice%"=="3" (
    call "启动_API服务.bat"
    goto menu
)
if "%choice%"=="0" exit /b 0

echo 无效选择，请重新输入。
pause
goto menu
"""
    _write_text_crlf(Path(staging_dir) / "启动菜单.bat", menu)


def write_readme(staging_dir):
    readme = """GPT-SoVITS v2ProPlus 绿色整合包说明

使用方式
1. 建议解压到英文或中文均可的短路径，例如 D:\\GPT-SoVITS-Portable。
2. 双击 启动菜单.bat。
3. 按菜单选择：
   1 推理WebUI: http://127.0.0.1:9872/
   2 训练WebUI: http://127.0.0.1:9874/
   3 API服务: http://127.0.0.1:9880/docs

默认模型
- GPT: GPT_SoVITS/pretrained_models/s1v3.ckpt
- SoVITS: GPT_SoVITS/pretrained_models/v2Pro/s2Gv2ProPlus.pth

打包说明
- 本包不包含原项目中的三轮训练 logs、训练权重、ASR 输出、切片输出和角色映射缓存。
- 参考音频目录作为示例素材保留。
- 如需使用自定义 GPT 权重，请放入 GPT_weights_v2ProPlus 或对应 GPT_weights* 目录。
- 如需使用自定义 SoVITS 权重，请放入 SoVITS_weights_v2ProPlus 或对应 SoVITS_weights* 目录。
- 运行日志会写入 logs/startup。
"""
    _write_text_crlf(Path(staging_dir) / "绿色包说明.txt", readme)


def rewrite_users_pth(staging_dir):
    users_pth = Path(staging_dir) / "py312" / "Lib" / "site-packages" / "users.pth"
    if not users_pth.parent.exists():
        return
    content = "\n".join(
        [
            "../../..",
            "../../../GPT_SoVITS/BigVGAN",
            "../../../tools",
            "../../../tools/asr",
            "../../../GPT_SoVITS",
            "../../../tools/uvr5",
            "",
        ]
    )
    users_pth.write_text(content, encoding="utf-8")


def ensure_runtime_empty_dirs(staging_dir):
    staging_dir = Path(staging_dir)
    for rel_dir in RUNTIME_EMPTY_DIRS:
        directory = staging_dir / rel_dir
        directory.mkdir(parents=True, exist_ok=True)


def remove_stale_runtime_files(staging_dir):
    staging_dir = Path(staging_dir)
    for rel_path in ["character_map.json"]:
        path = staging_dir / rel_path
        if path.exists():
            path.unlink()


def prepare_staging_overrides(staging_dir):
    staging_dir = Path(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)
    remove_stale_runtime_files(staging_dir)
    ensure_runtime_empty_dirs(staging_dir)
    write_weight_json(staging_dir)
    write_start_menu(staging_dir)
    write_readme(staging_dir)
    rewrite_users_pth(staging_dir)


def run_startup_check(staging_dir, mode="all", skip_cuda=False):
    command = [
        str(Path(staging_dir) / "py312" / "python.exe"),
        "-u",
        "tools/startup_check.py",
        "--mode",
        mode,
        "--skip-ports",
    ]
    if skip_cuda:
        command.append("--skip-cuda")
    completed = subprocess.run(command, cwd=staging_dir, text=True, capture_output=True)
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        raise RuntimeError(f"startup_check failed for mode={mode}\n{output}")
    return output


def create_zip_with_tar(staging_dir, dist_dir):
    staging_dir = Path(staging_dir).resolve()
    dist_dir = Path(dist_dir).resolve()
    zip_path = dist_dir / f"{staging_dir.name}.zip"
    if zip_path.exists():
        zip_path.unlink()

    command = [
        "tar.exe",
        "-a",
        "-cf",
        str(zip_path),
        "-C",
        str(staging_dir.parent),
        staging_dir.name,
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        output = (completed.stdout or "") + (completed.stderr or "")
        raise RuntimeError(f"tar.exe zip failed with code {completed.returncode}\n{output}")
    return zip_path


def build_portable_package(root, date_stamp=None, skip_checks=False, skip_cuda=False, skip_zip=False):
    root = Path(root).resolve()
    date_stamp = date_stamp or datetime.now().strftime("%Y%m%d")
    dist_dir = root / "dist"
    staging_parent = dist_dir / "_staging"
    package_name = f"{PACKAGE_PREFIX}-{date_stamp}"
    staging_dir = staging_parent / package_name

    dist_dir.mkdir(parents=True, exist_ok=True)
    staging_parent.mkdir(parents=True, exist_ok=True)
    _remove_if_exists(staging_dir, staging_parent)

    copy_project_to_staging(root, staging_dir)
    prepare_staging_overrides(staging_dir)

    if not skip_checks:
        run_startup_check(staging_dir, "all", skip_cuda=skip_cuda)

    if skip_zip:
        return PackageResult(staging_dir=staging_dir, zip_path=None)

    try:
        zip_path = create_zip_with_tar(staging_dir, dist_dir)
        return PackageResult(staging_dir=staging_dir, zip_path=zip_path)
    except Exception as exc:
        return PackageResult(staging_dir=staging_dir, zip_path=None, zip_error=str(exc))


def main(argv=None):
    parser = argparse.ArgumentParser(description="构建 GPT-SoVITS Windows 绿色整合包")
    parser.add_argument("--root", default=".", help="项目根目录")
    parser.add_argument("--date", default=None, help="包名日期，例如 20260611")
    parser.add_argument("--skip-checks", action="store_true", help="跳过 staging 启动预检")
    parser.add_argument("--skip-cuda", action="store_true", help="预检时跳过 CUDA 检测")
    parser.add_argument("--skip-zip", action="store_true", help="只生成 staging 目录，不压缩")
    args = parser.parse_args(argv)

    result = build_portable_package(
        args.root,
        date_stamp=args.date,
        skip_checks=args.skip_checks,
        skip_cuda=args.skip_cuda,
        skip_zip=args.skip_zip,
    )

    print(f"[OK] staging: {result.staging_dir}")
    if result.zip_path:
        print(f"[OK] zip: {result.zip_path}")
    elif result.zip_error:
        print("[WARN] zip 压缩失败，已保留 staging 目录。可安装 7-Zip 后二次压缩。")
        print(result.zip_error)
    else:
        print("[INFO] 已按参数跳过 zip 压缩。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
