# GPT-SoVITS 一键部署说明

Windows 新设备部署入口:

```bat
deploy.bat
```

脚本会要求选择部署模式，不设置默认项:

1. `软链接复用`: 输入已有 GPT-SoVITS 示例目录，把可复用目录以 junction 方式链接到当前仓库，速度最快且节省空间。
2. `复制复用`: 输入已有 GPT-SoVITS 示例目录，把可复用目录复制到当前仓库，适合迁移后独立运行。
3. `全新安装`: 自动创建/复用 conda 环境，调用现有 `install.ps1` 安装依赖、PyTorch 和模型数据。

复用模式会处理这些常见资源: `runtime`、`py312`、`.venv`、`GPT_SoVITS/pretrained_models`、`GPT_SoVITS/text/G2PWModel`、`tools/uvr5/uvr5_weights`、`tools/asr/models`、`GPT_weights*`、`SoVITS_weights*`、`logs`、`output`。

全新安装模式要求系统已安装 Miniforge/Anaconda，并且 `conda` 可在命令行中直接访问。

NVIDIA 显卡兼容性:

- 全新安装模式通过 Windows CIM 检测显卡名称；安装后的最终 CUDA 能力由包内 PyTorch 探针确认。
- 检测到 RTX 50 系、Blackwell 或 SM 12.x GPU 时，脚本会阻止选择 `CU126`，要求使用 `CU128` 或显式选择 `CPU`。
- 软链接/复制模式如果复用了 `runtime`、`py312` 或 `.venv`，脚本会读取该环境的 `torch.version.cuda`；在 RTX 50/Blackwell 上低于 12.8 会中止并提示改用 `CU128` 环境。
- 如果安装后包内 PyTorch 探针不满足所选 CUDA 配置，脚本会失败并提示修复运行时或驱动，不会静默回退到 CPU。

部署后启动:

```bat
go-webui.bat
```

`go-webui.bat` 会按顺序寻找 `runtime\python.exe`、`py312\python.exe`、`.venv\Scripts\python.exe`。如果使用全新安装模式，它会读取本机生成的 `deploy.env.bat` 并通过 conda 环境启动；该文件已被 `.gitignore` 忽略。
