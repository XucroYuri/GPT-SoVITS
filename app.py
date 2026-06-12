import os
import sys
import threading
import uvicorn

now_dir = os.getcwd()
sys.path.append(now_dir)
from tools.startup_bootstrap import apply_startup_patches

apply_startup_patches()

import api_v2
from GPT_SoVITS import inference_webui

def start_service():
    uvicorn.run(app=api_v2.APP, host="127.0.0.1", port=9880, workers=1)

def start_gradio():
    port = getattr(inference_webui, "infer_ttswebui", 9872)
    is_share = getattr(inference_webui, "is_share", False)
    while True:
        try:
            inference_webui.app.queue().launch(
                server_name="0.0.0.0",
                inbrowser=True,
                share=is_share,
                server_port=port,
                quiet=True,
            )
            break
        except OSError:
            port += 1

if __name__ == "__main__":
    print(
        "提示: app.py 是兼容组合入口，默认建议使用 启动_推理WebUI.bat 或 启动_API服务.bat 分开启动。",
        flush=True,
    )
    fastapi_thread = threading.Thread(target=start_service)
    gradio_thread = threading.Thread(target=start_gradio)

    fastapi_thread.start()
    gradio_thread.start()

    fastapi_thread.join()
    gradio_thread.join()
