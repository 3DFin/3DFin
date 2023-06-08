import subprocess
from pathlib import Path
from typing import Callable, Any

from hatchling.builders.plugin.interface import BuilderInterface




class PyInstalllerBuilder(BuilderInterface):
    
    def __init__(self, *args, **kwargs):
        """Init the hook, generate files."""
        super().__init__(*args, **kwargs)

    def get_version_api(self) -> dict[str, Callable]:
        return {"standard": self._pyinstaller_build}
    
    def _pyinstaller_build(self,  directory: str, **build_data: Any) -> str:
        self._pyinstaller_subprocess("pyinstaller/options.spec") # "-n NAME" for output and use call
        return "dist/3DFin.exe"

    def _pyinstaller_subprocess(self, input_path: Path):
        pyinstaller_process = subprocess.Popen(
            ["pyinstaller", str(input_path)],
            stdout=subprocess.PIPE, # do not pipe stderr with pyinstaller of it will end to an infinite loop!
            text=True
        )
        with pyinstaller_process.stdout:
            for line in iter(pyinstaller_process.stdout.readline, ""):
                self.app.display_info(line)
        exit_code = pyinstaller_process.wait()
        if exit_code != 0:
            raise Exception