from pathlib import Path

import pycc
from PySide6.QtCore import QEventLoop

from three_d_fin.cloudcompare.plugin_processing import CloudComparePluginProcessing
from three_d_fin.gui.application import Application
from three_d_fin.processing.configuration import FinConfiguration


class ThreeDFinCC(pycc.PythonPluginInterface):
    """Define a Plugin for CloudCompare-PythonRuntime."""

    def __init__(self):
        """Construct the object."""
        pycc.PythonPluginInterface.__init__(self)

    def getIcon(self) -> str:
        """Get the path to the plugin icon.

        Returns
        -------
        path : str
            the string representation of the path to the plugin icon.

        """
        return str((Path(__file__).parents[0] / "assets" / "3dfin_logo_plugin.png").resolve())

    def getActions(self) -> list[pycc.Action]:
        """List of actions exposed by the plugin."""
        return [pycc.Action(name="3D Forest INventory", icon=self.getIcon(), target=main)]


def _create_app_and_run(plugin_processing: CloudComparePluginProcessing, scalar_fields: list[str]):
    """Encapsulate the 3DFin GUI and processing.

    Parameters
    ----------
    plugin_processing : CloudComparePluginProcessing
        The instance of FinProcessing dedicated to CloudCompare (as a plugin)
    scalar_fields : list[str]
        A list of scalar field names. This list will feed the QComboBox inside
        the 3DFin GUI.

    """
    plugin_widget = Application(plugin_processing, file_externally_defined=True, cloud_fields=scalar_fields)
    loop = QEventLoop()
    plugin_widget.show()
    plugin_widget.set_event_loop(loop)
    loop.exec_()


def main() -> None:
    """3DFin CloudCompare Plugin main action."""
    cc = pycc.GetInstance()

    entities = cc.getSelectedEntities()

    if not entities or len(entities) > 1:
        raise RuntimeError("Please select one point cloud")

    point_cloud = entities[0]

    if not isinstance(point_cloud, pycc.ccPointCloud):
        raise RuntimeError("Selected entity should be a point cloud")

    # List all scalar fields to feed the QComboBox in the interface.
    scalar_fields: list[str] = []
    for i in range(point_cloud.getNumberOfScalarFields()):
        scalar_fields.append(point_cloud.getScalarFieldName(i))

    plugin_processing = CloudComparePluginProcessing(cc, point_cloud, FinConfiguration())

    cc.freezeUI(True)
    try:
        _create_app_and_run(plugin_processing, scalar_fields)
    except Exception:
        raise RuntimeError("Something went wrong!") from None
    finally:
        cc.freezeUI(False)
        cc.updateUI()
