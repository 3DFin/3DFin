import platform
from typing import Optional

import numpy as np
import pycc

from three_d_fin.gui.layout import Application


class ThreeDFinCC(pycc.PythonPluginInterface):
    """Define a CloudCompare-PythonPlugin Plugin (sic.)."""

    def __init__(self):
        """Construct the object."""
        pycc.PythonPluginInterface.__init__(self)

    def getActions(self) -> list[pycc.Action]:
        """List of actions exposed by the plugin."""
        return [pycc.Action(name="3DFin", target=main)]


class CloudComparePluginProcessing:
    """Implement the FinProcessing interface for CloudCompare in a plugin context."""

    base_group: pycc.ccHObject

    delayed_add_to_db: list[tuple[pycc.ccHObject, bool]] = list()

    def _construct_output_path(self):
        pass

    def _pre_processing_hook(self):
        self.base_group = self.point_cloud.getParent()

    def _post_processing_hook(self):
        # TODO delay all AddToDb call here
        pass

    def _load_base_cloud(self):
        pass

    def _get_xyz_z0_from_base(self) -> np.ndarray:
        return np.c_[
            self.point_cloud.points(),
            self.point_cloud.getScalarField(
                self.point_cloud.getScalarFieldIndexByName(self.config.basic.z0_name)
            ).asArray(),
        ]

    def _get_xyz_from_base(self) -> np.ndarray:
        # TODO(RJ) double conversion is only needed for DTM processing,
        # But maybe it's worth generalizing it.
        # CSF expects also fortran type arrays.
        return self.point_cloud.points().astype(np.double)

    def _export_dtm(self, dtm: np.ndarray):
        cloud_dtm = pycc.ccPointCloud(dtm[:, 0], dtm[:, 1], dtm[:, 2])
        cloud_dtm.setName("dtm")
        cloud_dtm.setEnabled(False)
        self.base_group.addChild(cloud_dtm)
        self.cc_instance.addToDB(cloud_dtm)

    def _export_stripe(self, clust_stripe: np.ndarray):
        cloud_stripe = pycc.ccPointCloud(
            clust_stripe[:, 0], clust_stripe[:, 1], clust_stripe[:, 2]
        )
        cloud_stripe.setName("Stems in stripe")
        CloudComparePluginProcessing.write_sf(
            cloud_stripe, clust_stripe[:, -1], "tree_ID"
        )
        cloud_stripe.setCurrentDisplayedScalarField(0)
        cloud_stripe.toggleSF()
        cloud_stripe.setEnabled(False)
        self.base_group.addChild(cloud_stripe)
        self.cc_instance.addToDB(cloud_stripe)

    def _enrich_base_cloud(
        self, assigned_cloud: np.ndarray, z0_values: Optional[np.ndarray]
    ):
        CloudComparePluginProcessing.write_sf(
            self.point_cloud, assigned_cloud[:, 5], "dist_axes"
        )
        CloudComparePluginProcessing.write_sf(
            self.point_cloud, assigned_cloud[:, 4], "tree_ID"
        )
        self.point_cloud.setEnabled(False)

        if not self.config.misc.is_normalized:
            # In the case the user still want to use our CSF normalization but already have
            # a field called Z0, adding the field with the same name will raise an exception.
            # So we have to check its existance before. if it's exist, the value is putted in
            # "Z0_dtm" scalar field
            # TODO: Maybe name this field in accordance with z0_name value
            if self.base_cloud.getScalarFieldIndexByName("Z0") == -1:
                CloudComparePluginProcessing.write_sf(self.point_cloud, z0_values, "Z0")
            else:
                z0_dtm_id = self.base_cloud.getScalarFieldIndexByName("Z0_dtm")
                if z0_dtm_id != -1:
                    CloudComparePluginProcessing.base_group.deleteScalarField(z0_dtm_id)
                CloudComparePluginProcessing.write_sf(
                    self.point_cloud, z0_values, "Z0_dtm"
                )

    def _export_tree_height(self, tree_heights: np.ndarray):
        cloud_tree_heights = pycc.ccPointCloud(
            tree_heights[:, 0], tree_heights[:, 1], tree_heights[:, 2]
        )
        cloud_tree_heights.setName("Highest points")
        CloudComparePluginProcessing.write_sf(
            cloud_tree_heights, tree_heights[:, 3], "z0"
        )
        CloudComparePluginProcessing.write_sf(
            cloud_tree_heights, tree_heights[:, 4], "deviated"
        )
        cloud_tree_heights.setPointSize(8)
        z0 = cloud_tree_heights.getScalarField(0)  # z0

        # Add label with z0 values
        for i in range(len(cloud_tree_heights.points())):
            hlabel = pycc.cc2DLabel(f"point{i}")
            hlabel.addPickedPoint(cloud_tree_heights, i)
            value = round(z0.asArray()[i], 2)
            hlabel.setName(f"{value:.2f}")
            hlabel.displayPointLegend(True)
            hlabel.toggleVisibility()
            hlabel.setDisplayedIn2D(False)
            cloud_tree_heights.addChild(hlabel)
            self.cc_instance.addToDB(hlabel)

        # Set black color everywhere
        cloud_tree_heights.setColor(0, 0, 0, 255)
        cloud_tree_heights.toggleColors()
        self.base_group.addChild(cloud_tree_heights)
        self.cc_instance.addToDB(cloud_tree_heights, autoExpandDBTree=False)

    def _export_circles(self, circles_coords: np.ndarray):
        cloud_circles = pycc.ccPointCloud(
            circles_coords[:, 0], circles_coords[:, 1], circles_coords[:, 2]
        )
        cloud_circles.setName("Fitted sections")
        CloudComparePluginProcessing.write_sf(
            cloud_circles, circles_coords[:, 4], "tree_ID"
        )
        CloudComparePluginProcessing.write_sf(
            cloud_circles, circles_coords[:, 5], "sector_occupancy_percent"
        )
        CloudComparePluginProcessing.write_sf(
            cloud_circles, circles_coords[:, 6], "pts_inner_circle"
        )
        CloudComparePluginProcessing.write_sf(cloud_circles, circles_coords[:, 7], "Z0")
        CloudComparePluginProcessing.write_sf(
            cloud_circles, circles_coords[:, 8], "Diameter"
        )
        CloudComparePluginProcessing.write_sf(
            cloud_circles, circles_coords[:, 9], "outlier_prob"
        )
        CloudComparePluginProcessing.write_sf(
            cloud_circles, circles_coords[:, 10], "quality"
        )
        cloud_circles.toggleSF()
        cloud_circles.setCurrentDisplayedScalarField(6)  # = quality
        self.base_group.addChild(cloud_circles)
        self.cc_instance.addToDB(cloud_circles)

    def _export_axes(self, axes_points: np.ndarray, tilt: np.ndarray):
        cloud_axes = pycc.ccPointCloud(
            axes_points[:, 0], axes_points[:, 1], axes_points[:, 2]
        )
        cloud_axes.setName("Axes")
        CloudComparePluginProcessing.write_sf(cloud_axes, tilt, "tilting_degree")
        cloud_axes.toggleSF()
        cloud_axes.setCurrentDisplayedScalarField(0)  # = tilting_degree
        cloud_axes.setEnabled(False)
        self.base_group.addChild(cloud_axes)
        self.cc_instance.addToDB(cloud_axes)

    def _export_tree_locations(
        self, tree_locations: np.ndarray, dbh_values: np.ndarray
    ):
        cloud_tree_locations = pycc.ccPointCloud(
            tree_locations[:, 0],
            tree_locations[:, 1],
            tree_locations[:, 2],
        )
        cloud_tree_locations.setName("Tree locator")
        cloud_tree_locations.setPointSize(8)
        CloudComparePluginProcessing.write_sf(
            cloud_tree_locations, dbh_values.reshape(-1), "dbh"
        )
        cloud_tree_locations.setColor(255, 0, 255, 255)
        cloud_tree_locations.toggleColors()
        dbh = cloud_tree_locations.getScalarField(0)  # dbh

        for i in range(len(cloud_tree_locations.points())):
            dlabel = pycc.cc2DLabel(f"point{i}")
            dlabel.addPickedPoint(cloud_tree_locations, i)
            value = round(dbh.asArray()[i], 3)
            if value == 0.0:
                dlabel.setName("Non Reliable")
            else:
                dlabel.setName(f"{value:.3f}")
            dlabel.displayPointLegend(True)
            dlabel.toggleVisibility()
            dlabel.setDisplayedIn2D(False)
            cloud_tree_locations.addChild(dlabel)
            self.cc_instance.addToDB(dlabel)

        self.base_group.addChild(cloud_tree_locations)
        self.cc_instance.addToDB(cloud_tree_locations, autoExpandDBTree=False)


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
    # FIX for HidPI support on windows 10+
    # The "bug" was sneaky for two reasons:
    # - First, you should turn the DpiAwareness value to a counter intuitive value
    # in other context you would assume to turn Dpi awarness at least >= 1 (PROCESS_SYSTEM_DPI_AWARE)
    # but here, with TK the right value is 0 (PROCESS_DPI_UNAWARE) maybe because DPI is handled by CC process
    # - Second, you can't use the usual SetProcessDpiAwareness function here because it could not be redefined
    # when defined once somewhere (TODO: maybe we could try to redefine it at startup of CC-PythonPlugin see if it works)
    # so we have to force it for the current thread with this one:
    # TODO: we do not know how it's handled in other OSes.
    import ctypes

    awareness_code = ctypes.c_int()
    if platform.system() == "Windows" and (
        platform.release() == "10" or platform.release() == "11"
    ):
        import ctypes.wintypes  # reimport here, because sometimes it's not initialized

        ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness_code))
        if awareness_code.value > 0:
            ctypes.windll.user32.SetThreadDpiAwarenessContext(
                ctypes.wintypes.HANDLE(-1)
            )
    fin_app = Application(
        plugin_processing, file_externally_defined=True, cloud_fields=scalar_fields
    )
    fin_app.run()


def main():
    """Plugin main action."""
    cc = pycc.GetInstance()

    entities = cc.getSelectedEntities()
    print(f"Selected entities: {entities}")

    if not entities or len(entities) > 1:
        raise RuntimeError("Please select one point cloud")

    point_cloud = entities[0]

    if not isinstance(point_cloud, pycc.ccPointCloud):
        raise RuntimeError("Selected entity should be a point cloud")

    # List all scalar fields to feed dropdown menu in the interface
    scalar_fields: list[str] = []
    for i in range(point_cloud.getNumberOfScalarFields()):
        scalar_fields.append(point_cloud.getScalarFieldName(i))

    # TODO: Detect if a user already have computed something on this cloud
    # (based on scalar field and entities in the DBTree)
    # and propose to force recompute (erase) or suggest to duplicate the point cloud.

    # TODO: Handle big coodinates (could be tested but maybe wait for CC API update).
    plugin_functor = CloudComparePluginProcessing(cc, point_cloud)

    cc.freezeUI(True)
    try:
        pycc.RunInThread(_create_app_and_run, plugin_functor, scalar_fields)
        # _create_app_and_run(plugin_functor, scalar_fields)
    except Exception:
        raise RuntimeError(
            "Something went wrong"
        ) from None  # TODO: Catch exceptions into modals.
    cc.freezeUI(False)
    cc.updateUI()
