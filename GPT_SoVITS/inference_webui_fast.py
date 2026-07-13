"""Compatibility entrypoint for the unified custom inference WebUI.

The main launcher keeps accepting the historical "fast inference" option,
but both launch paths now render the same customized inference interface.
"""

from pathlib import Path
import runpy


runpy.run_path(str(Path(__file__).with_name("inference_webui.py")), run_name="__main__")
