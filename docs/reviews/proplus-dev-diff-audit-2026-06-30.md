# ProPlus Dev Diff Audit - 2026-06-30

Scope: `xucroyuri/proplus-hc-dev` against upstream-tracking `main`.

## Summary

- Product direction: Windows/py312 ProPlus portable branch.
- Kept: startup bootstrap/checks, Windows launch scripts, portable package builder, model default display, reference-audio metadata, six-column `.list` metadata workflow, and ignore rules for logs/models/audio/runtime artifacts.
- Cleaned: stale fork-support notes, local progress diary, Star History badge, experimental combined launcher, broad ERes2Net/UVR formatting churn, unrelated UI CSS changes, and English locale typo regressions.

## Valid Local Product Changes

- Training labels support both `wav_path|speaker_name|language|text` and `wav_path|speaker_name|language|text|emotion|remark`.
- Training preprocessing consumes only the first four fields, so `emotion` and `remark` remain metadata instead of model-conditioning inputs.
- Label correction UI can edit `emotion` and `remark`, apply a global character name, and save six-column `.list` files.
- Inference WebUI can read ASR `.list` metadata, filter/select reference audio by character/language, backfill text/character/emotion/remark, and optionally write metadata back to `.list` with a `.bak` backup.

## Risks And Follow-Ups

- `GPT_SoVITS/inference_webui.py` still carries a large UI diff; future upstream syncs should keep metadata helpers small and covered by tests before merging UI changes.
- Full repository tests may still depend on CUDA/NVCC or optional upstream runtime assets; targeted portable/metadata tests are the required gate for this branch.
- Large ignored local artifacts remain intentionally outside Git. Keep `.gitignore` and `git check-ignore` verification in the release checklist.

## Verification Targets

- `python -m pytest tests/test_list_metadata_helpers.py tests/test_subfix_list_metadata.py tests/test_asr_model_paths.py tests/test_inference_runtime_defaults.py`
- `python -m pytest tests/test_startup_check.py tests/test_startup_bootstrap.py tests/test_inference_model_defaults.py tests/test_portable_package.py tests/test_reference_audio_metadata.py tests/test_startup_scripts.py`
- `git diff --check main...xucroyuri/proplus-hc-dev`
