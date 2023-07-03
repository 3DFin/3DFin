import subprocess
from pathlib import Path
from typing import Any, Callable

from hatchling.builders.plugin.interface import BuilderInterface


class PyInstalllerBuilder(BuilderInterface):
    """Builder class to run Pyinstaller."""

    def __init__(self, *args, **kwargs):
        """Init the builder, generate files."""
        super().__init__(*args, **kwargs)

    def get_version_api(self) -> dict[str, Callable]:
        """Implement abstract parent method."""
        return {"standard": self._pyinstaller_build}

    def _pyinstaller_build(self, directory: str, **build_data: Any) -> str:
        self._pyinstaller_subprocess("pyinstaller/3DFin.spec")
        # One major issue with pyinstaller is that we can't override parameters
        # in spec file with command line flags...
        # so we are forced to use hardcoded 'name' parameters and the builder can't be
        # generic. we harcode the input_path as well even if we can use it as a parmeter
        return str(Path(self.root) / Path("dist/3DFin.exe"))

    def _pyinstaller_subprocess(self, input_path: Path):
        pyinstaller_process = subprocess.Popen(
            ["pyinstaller", str(input_path)],
            stdout=subprocess.PIPE,  # do not pipe stderr with pyinstaller of it will end to an infinite loop!
            text=True,
        )
        with pyinstaller_process.stdout:
            for line in iter(pyinstaller_process.stdout.readline, ""):
                self.app.display_info(line)
        exit_code = pyinstaller_process.wait()
        if exit_code != 0:
            raise Exception
