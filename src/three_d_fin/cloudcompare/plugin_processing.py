import sys
from pathlib import Path

import numpy as np
import pycc

from three_d_fin.cloudcompare.plugin_progress import CloudCompareProgress
from three_d_fin.processing.abstract_processing import FinProcessing
from three_d_fin.processing.configuration import FinConfiguration


class CloudComparePluginProcessing(FinProcessing):
    """Implement the FinProcessing interface for CloudCompare in a plugin context."""

    base_group: pycc.ccHObject

    group_name: str

    @staticmethod
    def write_sf(point_cloud: pycc.ccPointCloud, scalar_field: np.ndarray, name: str):
        """Write a scalar field on a pycc.PointCloud.

        Parameters
        ----------
        point_cloud : pycc.ccPointCloud
            Point cloud targetted by the 3DFin processing.
        scalar_field : np.ndarray
            Numpy vector discribing the scalar field.
        name: str
            Name of the scalar_field to write.
        """
        idx_sf = point_cloud.addScalarField(name)
        sf_array = point_cloud.getScalarField(idx_sf).asArray()
        sf_array[:] = scalar_field.astype(np.float32)[:]
        point_cloud.getScalarField(idx_sf).computeMinAndMax()

    def __init__(
        self,
        cc_instance: pycc.ccPythonInstance,
        point_cloud: pycc.ccPointCloud,
        config: FinConfiguration,
    ):
        """Construct the functor object.

        Parameters
        ----------
        cc_instance : pycc.ccPythonInstance
            Current cc application, wrapped by CloudCompare-PythonRuntime.
        point_cloud : pycc.ccPointCloud
            Point cloud targetted by the 3DFin processing.
        config: FinConfiguration
            The FinConfiguration object
        """
        self.base_cloud = point_cloud
        self.cc_instance = cc_instance
        self.progress = CloudCompareProgress(output=sys.stdout)
        super().__init__(config)

    def _construct_output_path(self):
        # We still use the stem attribute since in CC cloud could name could be based on filenames
        self.output_basepath = (
            Path(self.config.misc.output_dir) / Path(self.base_cloud.getName()).stem
        )
        self.group_name = f"{Path(self.base_cloud.getName()).stem}_3DFin"

    def _pre_processing_hook(self):
        # Be sure to load our custom colorscale
        color_scale_path = str(
            (Path(__file__).parents[0] / "assets" / "3dfin_color_scale.xml").resolve()
        )
        scale_manager = pycc.ccColorScalesManager.GetUniqueInstance()
        color_scale = pycc.ccColorScale.LoadFromXML(color_scale_path)
        scale_manager.addScale(color_scale)
        self.base_group = pycc.ccHObject(self.group_name)
        self.base_cloud.setEnabled(False)

    def _post_processing_hook(self):
        # Could be used to delay addToDB calls.
        self.cc_instance.addToDB(self.base_group)

    def _load_base_cloud(self):
        # This is already loaded at object instanciation.
        pass

    def _get_xyz_z0_from_base(self) -> np.ndarray:
        return np.c_[
            self.base_cloud.points(),
            self.base_cloud.getScalarField(
                self.base_cloud.getScalarFieldIndexByName(self.config.basic.z0_name)
            ).asArray(),
        ]

    def _get_xyz_from_base(self) -> np.ndarray:
        # TODO(RJ) double conversion is only needed for DTM processing,
        # But maybe it's worth generalizing it.
        return self.base_cloud.points().astype(np.double)

    def _export_dtm(self, dtm: np.ndarray):
        cloud_dtm = pycc.ccPointCloud(dtm[:, 0], dtm[:, 1], dtm[:, 2])
        cloud_dtm.copyGlobalShiftAndScale(self.base_cloud)
        cloud_dtm.setName("dtm")
        cloud_dtm.setEnabled(False)
        self.base_group.addChild(cloud_dtm)
        self.cc_instance.addToDB(cloud_dtm)

    def _export_stripe(self, clust_stripe: np.ndarray):
        cloud_stripe = pycc.ccPointCloud(
            clust_stripe[:, 0], clust_stripe[:, 1], clust_stripe[:, 2]
        )
        cloud_stripe.copyGlobalShiftAndScale(self.base_cloud)
        cloud_stripe.setName("Stems in stripe")
        CloudComparePluginProcessing.write_sf(
            cloud_stripe, clust_stripe[:, -1], "tree_ID"
        )
        cloud_stripe.setCurrentDisplayedScalarField(0)
        cloud_stripe.toggleSF()
        cloud_stripe.setEnabled(False)
        self.base_group.addChild(cloud_stripe)
        self.cc_instance.addToDB(cloud_stripe)

    def _enrich_base_cloud(self, assigned_cloud: np.ndarray):
        copy_base_cloud = pycc.ccPointCloud(self.base_cloud.getName())
        copy_base_cloud.copyGlobalShiftAndScale(self.base_cloud)
        copy_base_cloud.reserve(self.base_cloud.size())

        # Could be a pycc.ccPointCloud.clone() but we do not want to clone all SFs
        copy_base_cloud.addPoints(
            assigned_cloud[:, 0], assigned_cloud[:, 1], assigned_cloud[:, 2]
        )

        CloudComparePluginProcessing.write_sf(
            copy_base_cloud, assigned_cloud[:, 5], "dist_axes"
        )
        CloudComparePluginProcessing.write_sf(
            copy_base_cloud, assigned_cloud[:, 4], "tree_ID"
        )

        # Use assigned_cloud z0 anyway
        CloudComparePluginProcessing.write_sf(
            copy_base_cloud, assigned_cloud[:, 3], "Z0"
        )

        copy_base_cloud.toggleSF()
        copy_base_cloud.setCurrentDisplayedScalarField(0)  # dist_axes

        # Set our custom color scale
        copy_base_cloud.setEnabled(False)
        color_scale_uuid = "{25ec76a1-9b8d-4e4a-a129-21ae313ef8ba}"
        color_scale_manager = pycc.ccColorScalesManager.GetUniqueInstance()
        color_scale = color_scale_manager.getScale(color_scale_uuid)
        copy_base_cloud.getCurrentDisplayedScalarField().setColorScale(color_scale)

        self.base_group.addChild(copy_base_cloud)
        self.cc_instance.addToDB(copy_base_cloud)

    def _export_tree_height(self, tree_heights: np.ndarray):
        cloud_tree_heights = pycc.ccPointCloud(
            tree_heights[:, 0], tree_heights[:, 1], tree_heights[:, 2]
        )
        cloud_tree_heights.copyGlobalShiftAndScale(self.base_cloud)
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
        cloud_circles.copyGlobalShiftAndScale(self.base_cloud)
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
        cloud_axes.copyGlobalShiftAndScale(self.base_cloud)
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
        cloud_tree_locations.copyGlobalShiftAndScale(self.base_cloud)
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
                dlabel.setName(f"Tree {i+1} | Non Reliable")
            else:
                dlabel.setName(f"Tree {i+1} | {value:.3f}")
            dlabel.displayPointLegend(True)
            dlabel.toggleVisibility()
            dlabel.setDisplayedIn2D(False)
            cloud_tree_locations.addChild(dlabel)
            self.cc_instance.addToDB(dlabel)

        self.base_group.addChild(cloud_tree_locations)
        self.cc_instance.addToDB(cloud_tree_locations, autoExpandDBTree=False)

    def _export_tabular_data(
        self,
        config,
        output_basepath,
        X_c,
        Y_c,
        R,
        check_circle,
        sector_perct,
        n_points_in,
        sections,
        outliers,
        dbh_values,
        tree_locations,
        tree_heights,
        cloud_size,
        cloud_shape,
    ):
        """Revert the Global shift in tabular data when needed.

        If the base cloud was shifted, the coordinates are converted back in global ones
        before exporting the tabular data by simply calling the parent method.
        see parent method for more details on parmeters.
        """
        if self.base_cloud.isShifted():
            print("Cloud is shifted, correcting tabular data coordinates.")
            global_shift = self.base_cloud.getGlobalShift()
            global_scale = self.base_cloud.getGlobalScale()

            # Convert coordinates to global ones.
            X_c = X_c / global_scale - global_shift[0]
            Y_c = Y_c / global_scale - global_shift[1]
            R = R / global_scale
            tree_locations[:, 0] = tree_locations[:, 0] / global_scale - global_shift[0]
            tree_locations[:, 1] = tree_locations[:, 1] / global_scale - global_shift[1]
            tree_locations[:, 2] = tree_locations[:, 2] / global_scale - global_shift[2]
            tree_heights[:, 0] = tree_heights[:, 0] / global_scale - global_shift[0]
            tree_heights[:, 1] = tree_heights[:, 1] / global_scale - global_shift[1]
            tree_heights[:, 2] = tree_heights[:, 2] / global_scale - global_shift[2]

        print("Exporting tabular data")
        super()._export_tabular_data(
            config,
            output_basepath,
            X_c,
            Y_c,
            R,
            check_circle,
            sector_perct,
            n_points_in,
            sections,
            outliers,
            dbh_values,
            tree_locations,
            tree_heights,
            cloud_size,
            cloud_shape,
        )
