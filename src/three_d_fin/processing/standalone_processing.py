from pathlib import Path

import laspy
import numpy as np

from three_d_fin.processing.abstract_processing import FinProcessing


class StandaloneLASProcessing(FinProcessing):
    """Implement the FinProcessing interface for LAS files in a standalone context."""

    def _construct_output_path(self):
        basename_las = Path(self.config.misc.input_file).stem if self.config.misc.input_file is not None else "3DFin"
        self.output_basepath = Path(self.config.misc.output_dir) / Path(basename_las)

    def check_already_computed_data(self) -> bool:
        """Check for already computed data in target directory."""
        any_of = super().check_already_computed_data()
        # Check existence of las output.
        any_of |= Path(str(self.output_basepath) + "_dtm_points.las").exists()
        any_of |= Path(str(self.output_basepath) + "_stripe.las").exists()
        any_of |= Path(str(self.output_basepath) + "_tree_ID_dist_axes.las").exists()
        any_of |= Path(str(self.output_basepath) + "_tree_heights.las").exists()
        any_of |= Path(str(self.output_basepath) + "_circ.las").exists()
        any_of |= Path(str(self.output_basepath) + "_axes.las").exists()
        any_of |= Path(str(self.output_basepath) + "_tree_locator.las").exists()

        return any_of

    def _pre_processing_hook(self):
        pass

    def _post_processing_hook(self):
        pass

    def _load_base_cloud(self):
        self.base_cloud = laspy.read(str(self.config.misc.input_file.resolve()))

    def _get_xyz_z0_from_base(self) -> np.ndarray:
        return np.vstack(
            (
                self.base_cloud.x,
                self.base_cloud.y,
                self.base_cloud.z,
                self.base_cloud[self.config.basic.z0_name],
            )
        ).transpose()

    def _get_xyz_from_base(self) -> np.ndarray:
        return np.vstack((self.base_cloud.x, self.base_cloud.y, self.base_cloud.z)).transpose()

    def _export_dtm(self, dtm: np.ndarray):
        las_dtm_points = laspy.create(point_format=2, file_version="1.4")
        las_dtm_points.xyz = dtm[:, 0:3]
        las_dtm_points.write(str(self.output_basepath) + "_dtm_points.las")

    def _export_stripe(self, clust_stripe: np.ndarray):
        las_stripe = laspy.create(point_format=2, file_version="1.4")
        las_stripe.xyz = clust_stripe[:, 0:3]

        las_stripe.add_extra_dim(laspy.ExtraBytesParams(name="tree_ID", type=np.int32))
        las_stripe.tree_ID = clust_stripe[:, -1]
        las_stripe.write(str(self.output_basepath) + "_stripe.las")

    def _enrich_base_cloud(self, assigned_cloud: np.ndarray):
        extra_fields = list()

        # We have to check extra field existence before. It could be a cloud from a previous run
        # or user may already have defined these fields for a reason or another.
        if not hasattr(self.base_cloud, "dist_axes"):
            extra_fields.append(laspy.ExtraBytesParams(name="dist_axes", type=np.float64))
        if not hasattr(self.base_cloud, "tree_ID"):
            extra_fields.append(laspy.ExtraBytesParams(name="tree_ID", type=np.int32))

        # Batch addition of extra fields. It minimizes the memory allocation.
        self.base_cloud.add_extra_dims(extra_fields)

        self.base_cloud.dist_axes = assigned_cloud[:, 5]
        self.base_cloud.tree_ID = assigned_cloud[:, 4]

        if self.config.misc is not None and not self.config.misc.is_normalized:
            # In the case the user still want to use our CSF normalization but already have
            # a field called Z0, adding the field with the same name will raise an exception.
            # So we have to check its existence before.
            # In this case no need to ask if we want to override, since the whole enriched
            # cloud is saved in another file instance.
            if not hasattr(self.base_cloud, "Z0"):
                self.base_cloud.add_extra_dim(laspy.ExtraBytesParams(name="Z0", type=np.float64))
            self.base_cloud.Z0 = assigned_cloud[:, 3]

        if self.base_cloud.header.version < laspy.header.Version(major=1, minor=4):
            # The base file is maybe not in point_format == 6 but since it's a copy it won't hurt
            # the base file in itself.
            self.base_cloud = laspy.convert(self.base_cloud, point_format_id=2, file_version="1.4")

        self.base_cloud.write(str(self.output_basepath) + "_tree_ID_dist_axes.las")

    def _export_tree_height(self, tree_heights):
        las_tree_heights = laspy.create(point_format=2, file_version="1.4")
        las_tree_heights.xyz = tree_heights[:, 0:3]
        las_tree_heights.add_extra_dims(
            [
                laspy.ExtraBytesParams(name="z0", type=np.float64),
                laspy.ExtraBytesParams(name="deviated", type=np.int32),
            ]
        )
        las_tree_heights.z0 = tree_heights[:, 3]
        # Vertical deviation binary indicator.
        las_tree_heights.deviated = tree_heights[:, 4]

        las_tree_heights.write(str(self.output_basepath) + "_tree_heights.las")

    def _export_circles(self, circles_coords: np.ndarray):
        # LAS file containing circle coordinates.
        las_circ = laspy.create(point_format=2, file_version="1.4")
        las_circ.xyz = circles_coords[:, 0:3]

        las_circ.add_extra_dims(
            [
                laspy.ExtraBytesParams(name="tree_ID", type=np.int32),
                laspy.ExtraBytesParams(name="sector_occupancy_percent", type=np.float64),
                laspy.ExtraBytesParams(name="pts_inner_circle", type=np.int32),
                laspy.ExtraBytesParams(name="Z0", type=np.float64),
                laspy.ExtraBytesParams(name="Diameter", type=np.float64),
                laspy.ExtraBytesParams(name="outlier_prob", type=np.float64),
                laspy.ExtraBytesParams(name="quality", type=np.int32),
            ]
        )

        las_circ.tree_ID = circles_coords[:, 4]
        las_circ.sector_occupancy_percent = circles_coords[:, 5]
        las_circ.pts_inner_circle = circles_coords[:, 6]
        las_circ.Z0 = circles_coords[:, 7]
        las_circ.Diameter = circles_coords[:, 8]
        las_circ.outlier_prob = circles_coords[:, 9]
        las_circ.quality = circles_coords[:, 10]

        las_circ.write(str(self.output_basepath) + "_circ.las")

    def _export_axes(self, axes_points: np.ndarray, tilt: np.ndarray):
        las_axes = laspy.create(point_format=2, file_version="1.4")
        las_axes.xyz = axes_points[:, 0:3]
        las_axes.add_extra_dim(laspy.ExtraBytesParams(name="tilting_degree", type=np.float64))
        las_axes.tilting_degree = tilt

        las_axes.write(str(self.output_basepath) + "_axes.las")

    def _export_tree_locations(self, tree_locations: np.ndarray, dbh_values: np.ndarray):
        las_tree_locations = laspy.create(point_format=2, file_version="1.4")
        las_tree_locations.xyz = tree_locations[:, 0:3]
        las_tree_locations.add_extra_dim(laspy.ExtraBytesParams(name="diameters", type=np.float64))
        las_tree_locations.diameters = dbh_values[:, 0]

        las_tree_locations.write(str(self.output_basepath) + "_tree_locator.las")
