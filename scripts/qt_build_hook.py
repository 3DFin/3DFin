import subprocess
from pathlib import Path
from typing import Any, Generator

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def _pyuic_subprocess(input_path: Path, output_path: Path, import_from):
    subprocess.call(
        [
            "pyuic5",
            str(input_path),
            "-o",
            str(output_path),
            f"--import-from={import_from}",
            "--resource-suffix=",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )


def _pyrcc_subprocess(input_path: Path, output_path: Path):
    subprocess.call(
        ["pyrcc5", str(input_path), "-o", str(output_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )


class QtBuildHook(BuildHookInterface):
    """Simple build hook to generate py files from QT ui ones."""

    artifacts = []

    def __init__(self, *args, **kwargs):
        """Init the hook, generate files."""
        super().__init__(*args, **kwargs)
        try:
            self.src_folder = self.config["src_folder"]
        except KeyError:
            self.app.abort("[QT-hook] src_folder undefined")

        try:
            self.dest_folder = self.config["dest_folder"]
        except KeyError:
            self.app.abort("[QT-hook] dest_folder undefined")

        self.import_from = self.config.pop("import_from", ".")

        self._generate_ui()
        self._generate_rc()

    def _generate_ui(self):
        for ui_file in self._glob_ui():
            dest_file = self._dest_from_src(ui_file)
            _pyuic_subprocess(ui_file, dest_file, self.import_from)
            self.app.display_info(f"[QT-hook] mocking {ui_file}")
            self.artifacts.append(str(dest_file))

    def _generate_rc(self):
        for rc_file in self._glob_rc():
            dest_file = self._dest_from_src(rc_file)
            _pyrcc_subprocess(rc_file, dest_file)
            self.app.display_info(f"[QT-hook] generating {rc_file}")
            self.artifacts.append(str(dest_file))

    def _glob_ui(self) -> Generator[Path, None, None]:
        return Path(self.src_folder).glob("*.ui")

    def _glob_rc(self) -> Generator[Path, None, None]:
        return Path(self.src_folder).glob("*.qrc")

    def _dest_from_src(self, src: Path) -> Path:
        base_name = src.stem
        return Path(self.dest_folder) / Path(base_name + ".py")

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Override BuildHookInterface method."""
        build_data["artifacts"].extend(self.artifacts)
        self.app.display_debug(build_data)
