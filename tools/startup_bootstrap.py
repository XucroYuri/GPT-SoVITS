import os
import sys
from dataclasses import dataclass


@dataclass
class StartupPatchResult:
    wmi_disabled: bool = False
    machine_overridden: bool = False
    message: str = ""


def _is_enabled(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _is_disabled(value):
    return str(value).strip().lower() in {"0", "false", "no", "off"}


def _machine_from_env(environ):
    arch = environ.get("PROCESSOR_ARCHITEW6432") or environ.get("PROCESSOR_ARCHITECTURE")
    if not arch:
        return "AMD64"
    arch = str(arch).strip()
    return {"x86_64": "AMD64", "amd64": "AMD64", "arm64": "ARM64"}.get(arch.lower(), arch)


def apply_startup_patches(
    platform_module=None,
    environ=None,
    version_info=None,
    os_name=None,
    logger=print,
):
    """Apply early Windows startup patches before torch/torchaudio import."""
    if platform_module is None:
        import platform as platform_module
    if environ is None:
        environ = os.environ
    if version_info is None:
        version_info = sys.version_info
    if os_name is None:
        os_name = os.name

    mode = environ.get("GPT_SOVITS_DISABLE_WMI_PROBE", "auto")
    if _is_disabled(mode):
        return StartupPatchResult()

    should_patch = _is_enabled(mode) or (
        str(mode).strip().lower() == "auto"
        and os_name == "nt"
        and tuple(version_info[:2]) >= (3, 12)
        and hasattr(platform_module, "_wmi_query")
    )
    if not should_patch:
        return StartupPatchResult()

    def _disabled_wmi_query(*_args, **_kwargs):
        raise OSError("WMI query disabled during GPT-SoVITS startup")

    platform_module._wmi_query = _disabled_wmi_query
    if hasattr(platform_module, "_uname_cache"):
        platform_module._uname_cache = None

    machine_value = _machine_from_env(environ)
    platform_module.machine = lambda: machine_value

    message = f"startup bootstrap: disabled Windows WMI platform probe, machine={machine_value}"
    if logger:
        logger(message)
    return StartupPatchResult(wmi_disabled=True, machine_overridden=True, message=message)


if __name__ == "__main__":
    apply_startup_patches()
