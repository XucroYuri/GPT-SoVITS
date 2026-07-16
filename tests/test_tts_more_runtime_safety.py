from __future__ import annotations

import os
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tts_more"))


class WorkerRuntimeSafetyTests(unittest.TestCase):
    def test_worker_status_uses_torch_uuid_without_spawning_nvidia_smi(self) -> None:
        from app.workers import runtime

        class FakeCuda:
            is_available = staticmethod(lambda: True)
            current_device = staticmethod(lambda: 0)
            memory_allocated = staticmethod(lambda _index: 0)
            memory_reserved = staticmethod(lambda _index: 0)
            mem_get_info = staticmethod(lambda _index: (1024, 2048))
            get_device_properties = staticmethod(
                lambda index: types.SimpleNamespace(uuid=f"GPU-logical-{index}")
            )

        fake_torch = types.SimpleNamespace(
            cuda=FakeCuda(), version=types.SimpleNamespace(cuda="12.8")
        )
        environment = {key: value for key, value in os.environ.items() if key != "CUDA_VISIBLE_DEVICES"}
        with mock.patch.dict(sys.modules, {"torch": fake_torch}), mock.patch.dict(
            os.environ, environment, clear=True
        ), mock.patch.object(
            subprocess,
            "run",
            side_effect=AssertionError("ordinary worker status must not spawn nvidia-smi"),
        ):
            runtime._DEVICE_UUID_CACHE.clear()
            status = runtime.worker_runtime_status(loaded=False, model=None)

        self.assertEqual("GPU-logical-0", status["device_uuid"])

    def test_worker_status_uses_visible_uuid_when_torch_uuid_is_unavailable(self) -> None:
        from app.workers import runtime

        class FakeCuda:
            is_available = staticmethod(lambda: True)
            current_device = staticmethod(lambda: 0)
            memory_allocated = staticmethod(lambda _index: 0)
            memory_reserved = staticmethod(lambda _index: 0)
            mem_get_info = staticmethod(lambda _index: (1024, 2048))
            get_device_properties = staticmethod(
                lambda _index: (_ for _ in ()).throw(RuntimeError("uuid unavailable"))
            )

        fake_torch = types.SimpleNamespace(
            cuda=FakeCuda(), version=types.SimpleNamespace(cuda="12.8")
        )
        with mock.patch.dict(sys.modules, {"torch": fake_torch}), mock.patch.dict(
            os.environ, {**os.environ, "CUDA_VISIBLE_DEVICES": "GPU-abcdef"}, clear=True
        ), mock.patch.object(
            subprocess,
            "run",
            side_effect=AssertionError("ordinary worker status must not spawn nvidia-smi"),
        ):
            runtime._DEVICE_UUID_CACHE.clear()
            status = runtime.worker_runtime_status(loaded=False, model=None)

        self.assertEqual("GPU-abcdef", status["device_uuid"])


if __name__ == "__main__":
    unittest.main()
