from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DeployGpuPreflightTests(unittest.TestCase):
    def test_windows_gpu_preflight_uses_cim_without_invoking_nvidia_smi(self) -> None:
        deploy = (ROOT / "deploy.ps1").read_text(encoding="utf-8-sig")
        lowered = deploy.casefold()

        self.assertNotIn("nvidia-smi", lowered)
        self.assertIn("get-ciminstance", lowered)
        self.assertIn("win32_videocontroller", lowered)
        self.assertIn("torch.version.cuda", deploy)

    def test_fresh_install_runs_fail_closed_torch_probe_after_installer(self) -> None:
        deploy = (ROOT / "deploy.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("function Assert-InstalledTorchDeviceCompatible", deploy)
        probe_start = deploy.index("function Assert-InstalledTorchDeviceCompatible")
        probe_end = deploy.index("\nfunction ", probe_start + 1)
        probe = deploy[probe_start:probe_end]
        fresh_start = deploy.index("function Invoke-FreshInstall")
        fresh_end = deploy.index("\nfunction ", fresh_start + 1)
        fresh_install = deploy[fresh_start:fresh_end]

        self.assertIn("torch.cuda.is_available()", probe)
        self.assertIn("torch.version.cuda", probe)
        self.assertIn('"12.8"', probe)
        self.assertIn('"12.6"', probe)
        self.assertIn("Invoke-CheckedCommand -FilePath \"conda\"", probe)
        installer = 'Invoke-CheckedCommand -FilePath "conda" -Arguments $installArgs'
        final_probe = (
            "Assert-InstalledTorchDeviceCompatible -EnvName $CondaEnvName "
            "-SelectedDevice $Device"
        )
        self.assertIn(installer, fresh_install)
        self.assertIn(final_probe, fresh_install)
        self.assertLess(fresh_install.index(installer), fresh_install.index(final_probe))


if __name__ == "__main__":
    unittest.main()
