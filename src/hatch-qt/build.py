import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

QT_BASE_PATH = Path("src/hatch-qt/qtfiles")
QT_OUT_PATH = Path("src/three_d_fin/gui")


def _pyuic_subprocess(input_path: str, output_path: str):
    subprocess.Popen(
        [
            "pyuic5",
            str(input_path.resolve()),
            "-o",
            str(output_path.resolve()),
            "--import-from=three_d_fin.gui",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )


def _pyrcc_subprocess(input_path: str, output_path: str):
    subprocess.Popen(
        ["pyrcc5", str(input_path.resolve()), "-o", str(output_path.resolve())],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )


class QtBuildHook(BuildHookInterface):
    """Simple build hook to generate py files from QT ui ones."""

    def __init__(self, *args, **kwargs):
        """Init the hook, generate files."""
        super().__init__(*args, **kwargs)
        self._generate_ui()
        self._generate_rc()

    def _generate_ui(self):
        # TODO: should be in pyproject configuration instead of being harcoded here
        print(self.directory)
        _pyuic_subprocess(
            QT_BASE_PATH / "main_window.ui", QT_OUT_PATH / "main_window.py"
        )
        _pyuic_subprocess(QT_BASE_PATH / "expert_dlg.ui", QT_OUT_PATH / "expert_dlg.py")


    def _generate_rc(self):
        _pyrcc_subprocess(
            QT_BASE_PATH / "gui_ressources.qrc", QT_OUT_PATH / "gui_ressources_rc.py"
        )
