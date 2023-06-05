from pathlib import Path

import pycc
from PyQt5.QtCore import QEventLoop

from three_d_fin.cloudcompare.plugin_processing import CloudComparePluginProcessing
from three_d_fin.gui.application import Application


class ThreeDFinCC(pycc.PythonPluginInterface):
    """Define a CloudCompare-PythonPlugin Plugin (sic.)."""

    def __init__(self):
        """Construct the object."""
        pycc.PythonPluginInterface.__init__(self)
        # Be sure to load our custom colorscale
        color_scale_path = str(
            (Path(__file__).parents[0] / "assets" / "3dfin_color_scale.xml").resolve()
        )
        pycc.ccColorScale.LoadFromXML(color_scale_path)

    def getIcon(self) -> str:
        """Get the path to the plugin icon.

        Returns
        -------
        path : str
            the string representation of the path to the plugin icon
        """
        return str(
            (Path(__file__).parents[0] / "assets" / "3dfin_logo_plugin.png").resolve()
        )

    def getActions(self) -> list[pycc.Action]:
        """List of actions exposed by the plugin."""
        return [
            pycc.Action(name="3D Forest INventory", icon=self.getIcon(), target=main)
        ]


def _create_app_and_run(
    plugin_processing: CloudComparePluginProcessing, scalar_fields: list[str]
):
    """Encapsulate the 3DFin GUI and processing.

    It also embed a custom fix for the HiDPI support that is broken when using tk
    under the CloudCompare runtime. This function allow to run the fix and the app
    on a dedicated thread thanx to pycc.RunInThread.

    Parameters
    ----------
    plugin_processing : CloudComparePluginProcessing
        The instance of FinProcessing dedicated to CloudCompare (as a plugin)
    scalar_fields : list[str]
        A list of scalar field names. These list will feed the dropdown menu
        inside the 3DFin GUI.
    """
    plugin_widget = Application(
        plugin_processing, file_externally_defined=True, cloud_fields=scalar_fields
    )
    loop = QEventLoop()
    plugin_widget.show()
    plugin_widget.set_event_loop(loop)
    loop.exec_()


def main():
    """3DFin CloudCompare Plugin main action."""
    cc = pycc.GetInstance()

    entities = cc.getSelectedEntities()

    if not entities or len(entities) > 1:
        raise RuntimeError("Please select one point cloud")

    point_cloud = entities[0]

    if not isinstance(point_cloud, pycc.ccPointCloud):
        raise RuntimeError("Selected entity should be a point cloud")

    # List all scalar fields to feed dropdown menu in the interface
    scalar_fields: list[str] = []
    for i in range(point_cloud.getNumberOfScalarFields()):
        scalar_fields.append(point_cloud.getScalarFieldName(i))

    # TODO: Handle big coodinates (could be tested but maybe wait for CC API update).
    plugin_functor = CloudComparePluginProcessing(cc, point_cloud)

    cc.freezeUI(True)
    try:
        _create_app_and_run(plugin_functor, scalar_fields)
    except Exception:
        raise RuntimeError(
            "Something went wrong!"
        ) from None  # TODO: Catch exceptions into modals.
    finally:
        cc.freezeUI(False)
        cc.updateUI()
