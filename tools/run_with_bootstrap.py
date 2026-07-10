import os
import runpy
import sys
from pathlib import Path

from tools.startup_bootstrap import apply_startup_patches


def _target_args(argv):
    args = list(argv)
    if args and args[0] == "--":
        args = args[1:]
    while args and args[0] in {"-s", "-u", "-I"}:
        args = args[1:]
    return args


def main(argv=None):
    args = _target_args(sys.argv[1:] if argv is None else argv)
    if not args:
        print("用法: python tools/run_with_bootstrap.py -- <script.py> [args...]")
        return 2

    target = args[0]
    target_path = Path(target)
    if not target_path.exists():
        print(f"启动目标不存在: {target}")
        return 2

    apply_startup_patches()
    print(f"startup runner: pid={os.getpid()} target={target} args={args[1:]}", flush=True)
    sys.argv = args
    runpy.run_path(str(target_path), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
