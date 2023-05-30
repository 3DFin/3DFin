from pathlib import Path
from Q

import pycc

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
    plugin_processing = CloudComparePluginProcessing(cc, point_cloud)

    #cc.freezeUI(True)
    plugin_widget = Application(plugin_processing, True, scalar_fields)
    plugin_widget.show()
        #cc.freezeUI(False)
    #cc.updateUI()
