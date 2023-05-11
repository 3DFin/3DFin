from pathlib import Path

import numpy as np
import pycc

from three_d_fin.processing.abstract_processing import FinProcessing


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
        self, cc_instance: pycc.ccPythonInstance, point_cloud: pycc.ccPointCloud
    ):
        """Construct the functor object.

        Parameters
        ----------
        cc_instance : pycc.ccPythonInstance
            Current cc application, wrapped by CloudCompare-PythonPlugin.
        point_cloud : pycc.ccPointCloud
            Point cloud targetted by the 3DFin processing.
        """
        self.base_cloud = point_cloud
        self.cc_instance = cc_instance

    def check_already_computed_data(self) -> bool:
        """See base class documentation."""
        self._construct_output_path()

        any_of = False
        # Check for scalar fields....
        any_of |= self.base_cloud.getScalarFieldIndexByName("dist_axes") == -1
        any_of |= self.base_cloud.getScalarFieldIndexByName("tree_ID") == -1
        # Check existence of tabular output
        if self.config.misc.export_txt:
            any_of |= Path(str(self.output_basepath) + "_diameters.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_X_c.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_Y_c.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_check_circle.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_n_points_in.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_sector_perct.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_outliers.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_dbh_and_heights.txt").exists()
            any_of |= Path(str(self.output_basepath) + "_sections.txt").exists()
        else:
            any_of |= Path(str(self.output_basepath) + ".xlsx").exists()
        # Check existence of ini output
        any_of |= Path(str(self.output_basepath) + "_config.ini").exists()
        self.overwrite = any_of
        return any_of

    def _construct_output_path(self):
        # We still use the stem attribute since in CC cloud could name could be based on filenames
        self.output_basepath = (
            Path(self.config.misc.output_dir) / Path(self.base_cloud.getName()).stem
        )
        self.group_name = f"{Path(self.base_cloud.getName()).stem}_3DFin"

    def _pre_processing_hook(self):
        self.base_group = pycc.ccHObject(self.group_name)
        self.base_cloud.setEnabled(False)

    def _post_processing_hook(self):
        # Could be usedto delay addToDB calls.
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
        # CSF expects also fortran type arrays.
        return self.base_cloud.points().astype(np.double)

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

    def _enrich_base_cloud(self, assigned_cloud: np.ndarray):
        copy_base_cloud = pycc.ccPointCloud(self.base_cloud.getName())
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
