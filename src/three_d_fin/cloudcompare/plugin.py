import platform
import timeit
from pathlib import Path

import dendromatics as dm
import numpy as np
import pycc

from three_d_fin.gui.layout import Application
from three_d_fin.processing.configuration import FinConfiguration
from three_d_fin.processing.io import export_tabular_data


class ThreeDFinCC(pycc.PythonPluginInterface):
    """Define a CloudCompare-PythonPlugin Plugin (sic.)."""

    def __init__(self):
        """Construct the object."""
        pycc.PythonPluginInterface.__init__(self)

    def getActions(self) -> list[pycc.Action]:
        """List of actions exposed by the plugin."""
        return [pycc.Action(name="3DFin", target=main)]


class CCPluginFinProcessing:
    """3DFin processing functor.

    The Functor wrap current CC environement needed by 3DFin and __call__ method trigger
    the processing.
    """

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
        self.point_cloud = point_cloud
        self.cc_instance = cc_instance

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
            Name of the scalar_field to write
        """
        idx_sf = point_cloud.addScalarField(name)
        sf_array = point_cloud.getScalarField(idx_sf).asArray()
        sf_array[:] = scalar_field.astype(np.float32)[:]
        point_cloud.getScalarField(idx_sf).computeMinAndMax()

    def __call__(self, config: FinConfiguration):
        """3DFin processing.

        Parameters
        ----------
        config : FinConfiguration
            Processing parameters.
        """
        # -------------------------------------------------------------------------------------------------
        # NON MODIFIABLE. These parameters should never be modified by the user.
        # -------------------------------------------------------------------------------------------------

        X_field = 0  # Which column contains X field  - NON MODIFIABLE
        Y_field = 1  # Which column contains Y field  - NON MODIFIABLE
        Z_field = 2  # Which column contains Z field  - NON MODIFIABLE

        n_digits = 5  # Number of digits for voxel encoding.

        base_group = self.point_cloud.getParent()

        basepath_output = str(
            Path(config.misc.output_dir) / Path(self.point_cloud.getName())
        )
        print(f"Output path is set to {basepath_output}")

        t_t = timeit.default_timer()

        if config.misc.is_normalized:
            print(f"Using scalar field {config.basic.z0_name} (normalized height)")
            # convert CC file
            coords = np.c_[
                self.point_cloud.points(),
                self.point_cloud.getScalarField(
                    self.point_cloud.getScalarFieldIndexByName(config.basic.z0_name)
                ).asArray(),
            ]
            # Number of points and area occuped by the plot.
            print("---------------------------------------------")
            print("Analyzing cloud size...")
            print("---------------------------------------------")

            _, _, voxelated_ground = dm.voxelate(
                coords[coords[:, 3] < 0.5, 0:3],
                1,
                2000,
                n_digits,
                with_n_points=False,
                silent=False,
            )
            cloud_size = coords.shape[0] / 1000000
            cloud_shape = voxelated_ground.shape[0]
            print("   This cloud has", "{:.2f}".format(cloud_size), "millions points")
            print("   Its area is ", cloud_shape, "m^2")

            print("---------------------------------------------")
            print("Cloud is already normalized...")
            print("---------------------------------------------")

        else:
            coords = np.asfortranarray(self.point_cloud.points()).astype(np.double)
            # TODO(RJ) double conversion is only needed for DTM processing, but it could be
            # good to handle that in a better way.

            # Number of points and area occuped by the plot.
            print("---------------------------------------------")
            print("Analyzing cloud size...")
            print("---------------------------------------------")

            _, _, voxelated_ground = dm.voxelate(
                coords, 1, 2000, n_digits, with_n_points=False, silent=False
            )
            cloud_size = coords.shape[0] / 1000000
            cloud_shape = voxelated_ground.shape[0]
            print("   This cloud has", "{:.2f}".format(cloud_size), "millions points")
            print("   Its area is ", cloud_shape, "m^2")
            del voxelated_ground

            print("---------------------------------------------")
            print("Cloud is not normalized...")
            print("---------------------------------------------")

            if config.misc.is_noisy:
                print("---------------------------------------------")
                print("And there is noise. Reducing it...")
                print("---------------------------------------------")
                t = timeit.default_timer()
                # Noise elimination
                clean_points = dm.clean_ground(
                    coords,
                    config.expert.res_ground,
                    config.expert.min_points_ground,
                )

                elapsed = timeit.default_timer() - t
                print("        ", "%.2f" % elapsed, "s: denoising")

                print("---------------------------------------------")
                print("Generating a Digital Terrain Model...")
                print("---------------------------------------------")
                t = timeit.default_timer()
                # Extracting ground points and DTM ## MAYBE ADD VOXELIZATION HERE
                cloth_nodes = dm.generate_dtm(clean_points)

                elapsed = timeit.default_timer() - t
                print("        ", "%.2f" % elapsed, "s: generating the DTM")

            else:
                print("---------------------------------------------")
                print("Generating a Digital Terrain Model...")
                print("---------------------------------------------")
                t = timeit.default_timer()
                print(config.expert.res_cloth)

                # Extracting ground points and DTM
                cloth_nodes = dm.generate_dtm(
                    cloud=coords, cloth_resolution=config.expert.res_cloth
                )

                elapsed = timeit.default_timer() - t
                print("        ", "%.2f" % elapsed, "s: generating the DTM")

            print("---------------------------------------------")
            print("Cleaning and exporting the Digital Terrain Model...")
            print("---------------------------------------------")
            t = timeit.default_timer()
            # Cleaning the DTM
            dtm = dm.clean_cloth(cloth_nodes)

            # Exporting the DTM
            cloud = pycc.ccPointCloud(dtm[:, X_field], dtm[:, Y_field], dtm[:, Z_field])
            cloud.setName("dtm")
            cloud.setEnabled(False)
            base_group.addChild(cloud)
            self.cc_instance.addToDB(cloud)

            elapsed = timeit.default_timer() - t
            print("        ", "%.2f" % elapsed, "s: exporting the DTM")

            # Normalizing the point cloud
            print("---------------------------------------------")
            print("Normalizing the point cloud and running the algorithm...")
            print("---------------------------------------------")
            t = timeit.default_timer()
            z0_values = dm.normalize_heights(coords, dtm)
            coords = np.append(coords, np.expand_dims(z0_values, axis=1), 1)

            elapsed = timeit.default_timer() - t
            print("        ", "%.2f" % elapsed, "s: Normalizing the point cloud")

            elapsed = timeit.default_timer() - t_t
            print("        ", "%.2f" % elapsed, "s: Total preprocessing time")

        print("---------------------------------------------")
        print("1.-Extracting the stripe and peeling the stems...")
        print("---------------------------------------------")

        stripe = coords[
            (coords[:, 3] > config.basic.lower_limit)
            & (coords[:, 3] < config.basic.upper_limit),
            0:4,
        ]
        clust_stripe = dm.verticality_clustering(
            stripe,
            config.expert.verticality_scale_stripe,
            config.expert.verticality_thresh_stripe,
            config.expert.number_of_points,
            config.basic.number_of_iterations,
            config.expert.res_xy_stripe,
            config.expert.res_z_stripe,
            n_digits,
        )

        print("---------------------------------------------")
        print("2.-Computing distances to axes and individualizating trees...")
        print("---------------------------------------------")

        assigned_cloud, tree_vector, tree_heights = dm.individualize_trees(
            coords,
            clust_stripe,
            config.expert.res_z,
            config.expert.res_xy,
            config.basic.lower_limit,
            config.basic.upper_limit,
            config.expert.height_range,
            config.expert.maximum_d,
            config.expert.minimum_points,
            config.expert.distance_to_axis,
            config.expert.maximum_dev,
            config.expert.res_heights,
            n_digits,
            X_field,
            Y_field,
            Z_field,
            tree_id_field=-1,
        )

        print("  ")
        print("---------------------------------------------")
        print("3.-Exporting .LAS files including complete cloud and stripe...")
        print("---------------------------------------------")

        # Stripe
        cloud = pycc.ccPointCloud(
            clust_stripe[:, X_field], clust_stripe[:, Y_field], clust_stripe[:, Z_field]
        )
        cloud.setName("Stems in stripe")
        CCPluginFinProcessing.write_sf(cloud, clust_stripe[:, -1], "tree_ID")
        cloud.setCurrentDisplayedScalarField(0)
        cloud.toggleSF()
        cloud.setEnabled(False)
        base_group.addChild(cloud)
        self.cc_instance.addToDB(cloud)

        # Append new field to bas point cloud
        CCPluginFinProcessing.write_sf(
            self.point_cloud, assigned_cloud[:, 5], "dist_axes"
        )
        CCPluginFinProcessing.write_sf(
            self.point_cloud, assigned_cloud[:, 4], "tree_ID"
        )
        self.point_cloud.setEnabled(False)

        if config.misc.is_noisy:
            CCPluginFinProcessing.write_sf(self.point_cloud, assigned_cloud[:, 4], "Z0")

        t_las = timeit.default_timer()
        elapsed_las = timeit.default_timer() - t_las
        print("Total time:", "   %.2f" % elapsed_las, "s")

        # Tree heights
        cloud = pycc.ccPointCloud(
            tree_heights[:, X_field], tree_heights[:, Y_field], tree_heights[:, Z_field]
        )
        cloud.setName("Highest points")
        CCPluginFinProcessing.write_sf(cloud, tree_heights[:, 3], "z0")
        CCPluginFinProcessing.write_sf(cloud, tree_heights[:, 4], "deviated")
        cloud.setPointSize(8)
        z0 = cloud.getScalarField(0)  # z0

        # Add label with z0 values
        for i in range(len(cloud.points())):
            hlabel = pycc.cc2DLabel(f"point{i}")
            hlabel.addPickedPoint(cloud, i)
            value = round(z0.asArray()[i], 2)
            hlabel.setName(f"{value:.2f}")
            hlabel.displayPointLegend(True)
            hlabel.toggleVisibility()
            hlabel.setDisplayedIn2D(False)
            cloud.addChild(hlabel)
            self.cc_instance.addToDB(hlabel)

        # Set black color everywhere
        cloud.setColor(0, 0, 0, 255)
        cloud.toggleColors()
        base_group.addChild(cloud)
        self.cc_instance.addToDB(cloud, autoExpandDBTree=False)

        # stem extraction and curation
        print("---------------------------------------------")
        print("4.-Extracting and curating stems...")
        print("---------------------------------------------")

        xyz0_coords = assigned_cloud[
            (assigned_cloud[:, 5] < config.advanced.stem_search_diameter)
            & (assigned_cloud[:, 3] > config.advanced.minimum_height)
            & (
                assigned_cloud[:, 3]
                < config.advanced.maximum_height + config.advanced.section_wid
            ),
            :,
        ]
        stems = dm.verticality_clustering(
            xyz0_coords,
            config.expert.verticality_scale_stripe,
            config.expert.verticality_thresh_stripe,
            config.expert.number_of_points,
            config.basic.number_of_iterations,
            config.expert.res_xy_stripe,
            config.expert.res_z_stripe,
            n_digits,
        )[:, 0:6]

        # Computing circles
        print("---------------------------------------------")
        print("5.-Computing diameters along stems...")
        print("---------------------------------------------")

        sections = np.arange(
            config.advanced.minimum_height,
            config.advanced.maximum_height,
            config.advanced.section_len,
        )  # Range of uniformly spaced values within the specified interval

        (
            X_c,
            Y_c,
            R,
            check_circle,
            _,
            sector_perct,
            n_points_in,
        ) = dm.compute_sections(
            stems,
            sections,
            config.advanced.section_wid,
            config.expert.diameter_proportion,
            config.expert.point_threshold,
            config.expert.minimum_diameter,
            config.advanced.maximum_diameter,
            config.expert.point_distance,
            config.expert.number_points_section,
            config.expert.number_sectors,
            config.expert.m_number_sectors,
            config.expert.circle_width,
        )

        # Once every circle on every tree is fitted, outliers are detected.
        np.seterr(divide="ignore", invalid="ignore")
        outliers = dm.tilt_detection(X_c, Y_c, R, sections, w_1=3, w_2=1)
        np.seterr(divide="warn", invalid="warn")

        print("  ")
        print("---------------------------------------------")
        print("6.-Drawing circles and axes...")
        print("---------------------------------------------")

        t_las2 = timeit.default_timer()

        circ_coords = dm.generate_circles_cloud(
            X_c,
            Y_c,
            R,
            sections,
            check_circle,
            sector_perct,
            n_points_in,
            tree_vector,
            outliers,
            config.expert.minimum_diameter,
            config.advanced.maximum_diameter,
            config.expert.point_threshold,
            config.expert.number_sectors,
            config.expert.m_number_sectors,
            config.expert.circa_points,
        )

        cloud = pycc.ccPointCloud(
            circ_coords[:, X_field], circ_coords[:, Y_field], circ_coords[:, Z_field]
        )
        cloud.setName("Fitted sections")
        CCPluginFinProcessing.write_sf(cloud, circ_coords[:, 4], "tree_ID")
        CCPluginFinProcessing.write_sf(
            cloud, circ_coords[:, 5], "sector_occupancy_percent"
        )
        CCPluginFinProcessing.write_sf(cloud, circ_coords[:, 6], "pts_inner_circle")
        CCPluginFinProcessing.write_sf(cloud, circ_coords[:, 7], "Z0")
        CCPluginFinProcessing.write_sf(cloud, circ_coords[:, 8], "Diameter")
        CCPluginFinProcessing.write_sf(cloud, circ_coords[:, 9], "outlier_prob")
        CCPluginFinProcessing.write_sf(cloud, circ_coords[:, 10], "quality")
        cloud.toggleSF()
        cloud.setCurrentDisplayedScalarField(6)  # = quality
        base_group.addChild(cloud)
        self.cc_instance.addToDB(cloud)

        axes_point, tilt = dm.generate_axis_cloud(
            tree_vector,
            config.expert.axis_downstep,
            config.expert.axis_upstep,
            config.basic.lower_limit,
            config.basic.upper_limit,
            config.expert.p_interval,
            X_field,
            Y_field,
            Z_field,
        )

        cloud = pycc.ccPointCloud(
            axes_point[:, X_field], axes_point[:, Y_field], axes_point[:, Z_field]
        )
        cloud.setName("Axes")
        CCPluginFinProcessing.write_sf(cloud, tilt, "tilting_degree")
        cloud.toggleSF()
        cloud.setCurrentDisplayedScalarField(0)  # = tilting_degree
        cloud.setEnabled(False)
        base_group.addChild(cloud)
        self.cc_instance.addToDB(cloud)

        dbh_values, tree_locations = dm.tree_locator(
            sections,
            X_c,
            Y_c,
            tree_vector,
            sector_perct,
            R,
            outliers,
            n_points_in,
            config.expert.point_threshold,
            X_field,
            Y_field,
            Z_field,
        )

        cloud = pycc.ccPointCloud(
            tree_locations[:, X_field],
            tree_locations[:, Y_field],
            tree_locations[:, Z_field],
        )
        cloud.setName("Tree locator")
        cloud.setPointSize(8)
        CCPluginFinProcessing.write_sf(cloud, dbh_values.reshape(-1), "dbh")
        cloud.setColor(255, 0, 255, 255)
        cloud.toggleColors()
        dbh = cloud.getScalarField(0)  # dbh

        for i in range(len(cloud.points())):
            dlabel = pycc.cc2DLabel(f"point{i}")
            dlabel.addPickedPoint(cloud, i)
            value = round(dbh.asArray()[i], 3)
            if value == 0.0:
                dlabel.setName("Non Reliable")
            else:
                dlabel.setName(f"{value:.3f}")
            dlabel.displayPointLegend(True)
            dlabel.toggleVisibility()
            dlabel.setDisplayedIn2D(False)
            cloud.addChild(dlabel)
            self.cc_instance.addToDB(dlabel)

        base_group.addChild(cloud)
        self.cc_instance.addToDB(cloud, autoExpandDBTree=False)

        export_tabular_data(
            config,
            basepath_output,
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
        elapsed_las2 = timeit.default_timer() - t_las2
        print("Total time:", "   %.2f" % elapsed_las2, "s")

        elapsed_t = timeit.default_timer() - t_t

        config.to_config_file(Path(basepath_output + "_config.ini"))
        # -------------------------------------------------------------------------------------------------------------
        print("---------------------------------------------")
        print("End of process!")
        print("---------------------------------------------")
        print("Total time:", "   %.2f" % elapsed_t, "s")
        print("nº of trees:", X_c.shape[0])


def _create_app_and_run(
    plugin_functor: CCPluginFinProcessing, scalar_fields: list[str]
):
    """Encapsulate the 3DFin GUI and processing.

    It also embed a custom fix for the HiDPI support that is broken when using tk
    under the CloudCompare runtime. This function allow to run the fix and the app
    on a dedicated thread thanx to pycc.RunInThread.

    Parameters
    ----------
    plugin_functor : CCPluginFinProcessing
        The functor you want to run inside the 3DFin application.
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
    try:
        fin_app = Application(
            plugin_functor, file_externally_defined=True, cloud_fields=scalar_fields
        )
        fin_app.run()
    except Exception:  # TODO: Exception handling
        pass
    finally:
        print("cleaning and setting back current working directory to default")


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
    plugin_functor = CCPluginFinProcessing(cc, point_cloud)

    cc.freezeUI(True)
    # TODO: Catch exceptions into modals.
    pycc.RunInThread(_create_app_and_run, plugin_functor, scalar_fields)
    # _create_app_and_run(plugin_functor, scalar_fields)
    cc.freezeUI(False)
    cc.updateUI()
