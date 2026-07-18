from __future__ import annotations

import importlib.util
import io
import json
import re
import subprocess
import unittest
from contextlib import redirect_stderr
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_gate():
    path = ROOT / "tts_more" / "verify-release-asset-set.py"
    assert path.is_file(), "fork release gate is missing"
    spec = importlib.util.spec_from_file_location("verify_release_asset_set", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _expected_names() -> list[str]:
    archive = "GPT-SoVITS-0.2.0-test-windows-x64-cpu-bootstrap.zip"
    return [
        archive,
        f"{archive}.sha256",
        f"{archive}.spdx.json",
        f"{archive}.licenses.json",
        f"{archive}.provenance.json",
        f"{archive}.acceptance.json",
    ]


def _arguments(expected: list[str]) -> list[str]:
    return [
        "--repository",
        "XucroYuri/GPT-SoVITS",
        "--tag",
        "v0.2.0-test",
        *(argument for name in expected for argument in ("--expected-name", name)),
    ]


class PortableReleaseGateTests(unittest.TestCase):
    def test_runtime_probe_adds_the_upstream_gpt_source_root(self) -> None:
        runtime_lock = json.loads(
            (ROOT / "tts_more" / "locks" / "runtime.lock.json").read_text(encoding="utf-8")
        )
        component = json.loads(
            (ROOT / "tts_more" / "component.json").read_text(encoding="utf-8")
        )

        for probe in (runtime_lock["import_probe"], component["import_probe"]):
            self.assertIn("pathlib.Path.cwd() / 'GPT_SoVITS'", probe)
            self.assertLess(probe.index("sys.path.insert"), probe.index("from GPT_SoVITS"))

    def test_release_gate_accepts_exact_six_assets(self) -> None:
        gate = _load_gate()
        expected = _expected_names()

        def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                command, 0, stdout="\n".join(reversed(expected)) + "\n", stderr=""
            )

        self.assertEqual(0, gate.main(_arguments(expected), run=fake_run))

    def test_release_gate_rejects_concurrent_seventh_asset(self) -> None:
        gate = _load_gate()
        expected = _expected_names()

        def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="\n".join([*expected, "foreign-full.zip"]) + "\n",
                stderr="",
            )

        with redirect_stderr(io.StringIO()):
            self.assertNotEqual(0, gate.main(_arguments(expected), run=fake_run))

    def test_release_gate_rejects_six_assets_when_one_is_replaced(self) -> None:
        gate = _load_gate()
        expected = _expected_names()

        def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="\n".join([*expected[:-1], "foreign.zip"]) + "\n",
                stderr="",
            )

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertNotEqual(0, gate.main(_arguments(expected), run=fake_run))
        error = stderr.getvalue()
        self.assertIn("mismatch", error)
        self.assertIn(expected[-1], error)
        self.assertIn("foreign.zip", error)

    def test_release_workflow_audits_before_and_after_upload(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "portable-release.yml").read_text(
            encoding="utf-8"
        )
        publish = workflow.split("- name: Publish bootstrap assets only", 1)[1]
        upload = 'gh release upload "$GITHUB_REF_NAME" "${assets[@]}" --clobber'
        gate_call = '"$build_python" tts_more/verify-release-asset-set.py'

        self.assertIn("audit-release-assets --directory", workflow)
        self.assertIn("comm -23", publish)
        self.assertIn(upload, publish)
        self.assertIn(gate_call, publish)
        self.assertLess(publish.index(upload), publish.index(gate_call))
        self.assertIn('verify_asset_args+=(--expected-name "$asset_name")', publish)
        self.assertNotIn("release delete-asset", publish)

    def test_release_workflow_uses_locked_portable_build_tools(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "portable-release.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b",
            workflow,
        )
        self.assertEqual(2, workflow.count("uv sync --locked --project tts_more/build-tools"))
        self.assertIn(
            "UV_PROJECT_ENVIRONMENT: ${{ runner.temp }}\\tts-more-build-tools", workflow
        )
        self.assertIn(
            "UV_PROJECT_ENVIRONMENT: ${{ runner.temp }}/tts-more-build-tools", workflow
        )
        self.assertIn(
            "$buildPython = Join-Path $env:UV_PROJECT_ENVIRONMENT \"Scripts\\python.exe\"",
            workflow,
        )
        self.assertIn("$env:TTS_MORE_BUILD_PYTHON = $buildPython", workflow)
        self.assertIn("build_python=\"$UV_PROJECT_ENVIRONMENT/bin/python\"", workflow)
        self.assertNotRegex(
            workflow,
            re.compile(
                r"(?m)^\s*python\s+tts_more[\\/](?:portable_packages|verify-release-asset-set)\.py"
            ),
        )
        self.assertNotIn("pip install jsonschema", workflow)

    def test_release_workflow_checks_root_full_refusal_as_child_process(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "portable-release.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "$fullProbePowerShell = (Get-Process -Id $PID).Path", workflow
        )
        self.assertIn(
            "Start-Process -FilePath $fullProbePowerShell", workflow
        )
        self.assertIn(
            "-RedirectStandardOutput $fullProbeStdout", workflow
        )
        self.assertIn(
            "-RedirectStandardError $fullProbeStderr", workflow
        )
        self.assertIn(
            "$fullProbeExitCode = $fullProbeProcess.ExitCode",
            workflow,
        )
        self.assertIn("if ($fullProbeExitCode -eq 0)", workflow)
        self.assertIn('$fullProbeText -notmatch "profile=full"', workflow)
        self.assertNotIn("$blocked = $false", workflow)


if __name__ == "__main__":
    unittest.main()
