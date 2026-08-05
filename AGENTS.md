# GPT-SoVITS — AI Agent Onboarding Instructions

## Project Identity
- **Name**: GPT-SoVITS-WebUI
- **Type**: Fork of [RVC-Boss/GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) — upstream syncs to this repo's `main` branch
- **Stack**: Python 3.10-3.12, PyTorch, Gradio WebUI, FastAPI, ONNX Runtime, CTranslate2
- **Purpose**: Few-shot voice conversion and text-to-speech WebUI
- **Remote**: `origin` = XucroYuri/GPT-SoVITS (fork), `upstream` = RVC-Boss/GPT-SoVITS
- **License**: MIT

## Quick Reference (after initial setup)

```bash
pip install -r requirements.txt      # Install dependencies
python webui.py                      # Launch Gradio WebUI
python api_v2.py                     # Launch FastAPI server
python GPT_SoVITS/inference_cli.py   # CLI inference
```

## Architecture

```
WebUI Layer:
  webui.py             → Gradio WebUI (main entry point, 82K)
  api.py / api_v2.py   → FastAPI REST APIs
  GPT_SoVITS/inference_webui.py / inference_webui_fast.py → WebUI inference backends

Core Engine (GPT_SoVITS/):
  s1_train.py                     → Stage 1: AR (AutoRegressive) model training
  s2_train.py / s2_train_v3.py   → Stage 2: Diffusion/VAE model training
  s2_train_v3_lora.py            → Stage 2 with LoRA fine-tuning
  module/                         → Core neural network modules
  text/                           → Text processing (Chinese, Japanese, English, Cantonese)
  TTS_infer_pack/                 → TTS inference packaging
  AR/                             → AutoRegressive model
  BigVGAN/                        → BigVGAN vocoder
  f5_tts/                         → F5-TTS integration
  feature_extractor/              → Audio feature extraction (CNHuBERT, etc.)
  pretrained_models/              → Pretrained model downloading and loading

Tools (tools/):
  slice_audio.py / slicer2.py    → Audio slicing for training data prep
  asr/                            → ASR tools (FunASR-based)
  uvr5/                           → UVR5 voice accompaniment separation
  AP_BWE_main/                    → Audio bandwidth extension (24k→48k)
  denoise-model/                  → Audio denoising

Training Pipeline:
  Stage 1 → AR model (GPT-style autoregressive)
  Stage 2 → Diffusion/VAE model (SoVITS-style)
  Both stages → Full TTS/Voice Conversion model

Inference:
  GPT_SoVITS/inference_cli.py        → CLI inference
  GPT_SoVITS/inference_gui.py        → GUI inference (non-WebUI)
  GPT_SoVITS/stream_v2pro.py         → Streaming inference V2 Pro
```

## Critical Files

| File | Role |
|------|------|
| `webui.py` (82K) | Main Gradio WebUI entry point — all UI tabs |
| `api.py` / `api_v2.py` | FastAPI REST APIs for TTS/VC |
| `config.py` | Global configuration (paths, device, model settings) |
| `GPT_SoVITS/s1_train.py` | Stage 1 training (AR model) |
| `GPT_SoVITS/s2_train_v3.py` | Stage 2 training (Diffusion model) |
| `GPT_SoVITS/inference_webui.py` | WebUI inference backend |
| `GPT_SoVITS/inference_cli.py` | CLI inference entry point |
| `GPT_SoVITS/module/` | Core neural network modules |
| `GPT_SoVITS/text/` | Multilingual text processing pipeline |
| `GPT_SoVITS/TTS_infer_pack/` | TTS inference packaging utilities |
| `GPT_SoVITS/onnx_export.py` | ONNX model export |
| `requirements.txt` | Python dependencies (numpy<2.0, torch, gradio<5, transformers, etc.) |
| `tools/slice_audio.py` | Training audio preprocessing |
| `tools/uvr5/` | Ultimate Vocal Remover 5 integration |

## Development Rules

1. **Python version**: 3.10-3.12 only. Do NOT use Python 3.13+.
2. **Dependency constraints**: numpy<2.0, gradio<5, transformers>=4.43,<=4.50, peft<0.18.0, ctranslate2>=4.0,<5, av>=11
3. **Fork sync**: Keep fork-specific changes isolated. Sync upstream `main` regularly from `RVC-Boss/GPT-SoVITS`
4. **Branch strategy**: Create feature branches for all changes. `main` stays clean for upstream syncs.
5. **GPU required**: Training requires NVIDIA GPU with CUDA. Inference can run on CPU (slower) or GPU.
6. **Pretrained models**: Downloaded automatically to `GPT_SoVITS/pretrained_models/` on first run.
7. **Config**: Paths configured in `config.py`. Model weights go to `GPT_weights/` and `SoVITS_weights/` (gitignored).
8. **Logging**: Use Python `logging` module. Logs go to `logs/` directory.
9. **Security**: `.claude/settings.json` enforces `acceptEdits` mode — do not weaken deny rules without review.
10. **Testing**: Tests in `tests/` directory.

## Avoid

- Modifying upstream files without clear reason
- Hardcoding credentials or API keys
- Adding dependencies without clear justification
- Pushing directly to `main` without review
- Using `rm -rf`, `sudo`, `chown` (blocked by deny rules)
- Using Python features from 3.13+
- Training on CPU (waste of time — always use GPU)

## Key Dependencies

- **PyTorch** (with CUDA): Core deep learning framework
- **Gradio**: WebUI framework (v4.x, <5)
- **FastAPI**: REST API framework (v0.115.2+)
- **Transformers**: HuggingFace transformers (4.43-4.50)
- **FunASR**: Alibaba speech recognition toolkit
- **ONNX Runtime**: Model export/optimization
- **CTranslate2**: Fast inference engine (v4.x)
- **Librosa**: Audio processing
- **FFmpeg**: Audio/video encoding (via ffmpeg-python)
