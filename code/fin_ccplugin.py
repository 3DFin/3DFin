import timeit

import dendromatics as dm
import numpy as np
import pycc
import ctypes
from gui.gui_layout import Application


class TreeIndividualizationCC(pycc.PythonPluginInterface):
    def __init__(self):
        pycc.PythonPluginInterface.__init__(self)

    def getActions(self):
        return [pycc.Action(name="Tree Individualization", target=main_cloudcompare)]


class CCPluginFinProcessing:
    def __init__(self, cc_instance, point_cloud: pycc.ccPointCloud, z0_name):
        self.point_cloud = point_cloud
        self.cc_instance = cc_instance
        self.z0_name = z0_name

    @classmethod
    def write_sf(cls, point_cloud, scalar_field, name):
        idx_sf = point_cloud.addScalarField(name)
        sf_array = point_cloud.getScalarField(idx_sf).asArray()
        sf_array[:] = scalar_field.astype(np.float32)[:]
        point_cloud.getScalarField(idx_sf).computeMinAndMax()

    def __call__(self, fin_app: Application, params: dict):
        # -------------------------------------------------------------------------------------------------
        # NON MODIFIABLE. These parameters should never be modified by the user.
        # -------------------------------------------------------------------------------------------------

        X_field = 0  # Which column contains X field  - NON MODIFIABLE
        Y_field = 1  # Which column contains Y field  - NON MODIFIABLE
        Z_field = 2  # Which column contains Z field  - NON MODIFIABLE

        n_digits = 5  # Number of digits for voxel encoding.

        base_group = self.point_cloud.getParent()

        print(fin_app.copyright_info_1)
        print(fin_app.copyright_info_2)
        print(
            "See License at the bottom of 'About' tab for more details or visit <https://www.gnu.org/licenses/>"
        )

        t_t = timeit.default_timer()

        if params["misc"]["is_normalized"]:
            # convert CC file
            coords = np.c_[
                self.point_cloud.points(),
                self.point_cloud.getScalarField(
                    self.point_cloud.getScalarFieldIndexByName(self.z0_name)
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
            # Read .LAS file.
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

            if params["misc"]["is_noisy"]:
                print("---------------------------------------------")
                print("And there is noise. Reducing it...")
                print("---------------------------------------------")
                t = timeit.default_timer()
                # Noise elimination
                clean_points = dm.clean_ground(
                    coords,
                    params["expert"]["res_ground"],
                    params["expert"]["min_points_ground"],
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
                print(params["expert"]["res_cloth"])

                # Extracting ground points and DTM
                cloth_nodes = dm.generate_dtm(
                    cloud=coords, cloth_resolution=params["expert"]["res_cloth"]
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
            (coords[:, 3] > params["basic"]["lower_limit"])
            & (coords[:, 3] < params["basic"]["upper_limit"]),
            0:4,
        ]
        clust_stripe = dm.verticality_clustering(
            stripe,
            params["expert"]["verticality_scale_stripe"],
            params["expert"]["verticality_thresh_stripe"],
            params["expert"]["number_of_points"],
            params["basic"]["number_of_iterations"],
            params["expert"]["res_xy_stripe"],
            params["expert"]["res_z_stripe"],
            n_digits,
        )

        print("---------------------------------------------")
        print("2.-Computing distances to axes and individualizating trees...")
        print("---------------------------------------------")

        assigned_cloud, tree_vector, tree_heights = dm.individualize_trees(
            coords,
            clust_stripe,
            params["expert"]["res_z"],
            params["expert"]["res_xy"],
            params["basic"]["lower_limit"],
            params["basic"]["upper_limit"],
            params["expert"]["height_range"],
            params["expert"]["maximum_d"],
            params["expert"]["minimum_points"],
            params["expert"]["distance_to_axis"],
            params["expert"]["maximum_dev"],
            params["expert"]["res_heights"],
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

        if params["misc"]["is_noisy"]:
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
            (assigned_cloud[:, 5] < params["advanced"]["stem_search_diameter"])
            & (assigned_cloud[:, 3] > params["advanced"]["minimum_height"])
            & (
                assigned_cloud[:, 3]
                < params["advanced"]["maximum_height"]
                + params["advanced"]["section_wid"]
            ),
            :,
        ]
        stems = dm.verticality_clustering(
            xyz0_coords,
            params["expert"]["verticality_scale_stripe"],
            params["expert"]["verticality_thresh_stripe"],
            params["expert"]["number_of_points"],
            params["basic"]["number_of_iterations"],
            params["expert"]["res_xy_stripe"],
            params["expert"]["res_z_stripe"],
            n_digits,
        )[:, 0:6]

        # Computing circles
        print("---------------------------------------------")
        print("5.-Computing diameters along stems...")
        print("---------------------------------------------")

        sections = np.arange(
            params["advanced"]["minimum_height"],
            params["advanced"]["maximum_height"],
            params["advanced"]["section_len"],
        )  # Range of uniformly spaced values within the specified interval

        (
            X_c,
            Y_c,
            R,
            check_circle,
            second_time,
            sector_perct,
            n_points_in,
        ) = dm.compute_sections(
            stems,
            sections,
            params["advanced"]["section_wid"],
            params["expert"]["diameter_proportion"],
            params["expert"]["point_threshold"],
            params["expert"]["minimum_diameter"],
            params["advanced"]["maximum_diameter"],
            params["expert"]["point_distance"],
            params["expert"]["number_points_section"],
            params["expert"]["number_sectors"],
            params["expert"]["m_number_sectors"],
            params["expert"]["circle_width"],
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
            params["expert"]["minimum_diameter"],
            params["advanced"]["maximum_diameter"],
            params["expert"]["point_threshold"],
            params["expert"]["number_sectors"],
            params["expert"]["m_number_sectors"],
            params["expert"]["circa_points"],
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
            params["expert"]["axis_downstep"],
            params["expert"]["axis_upstep"],
            params["basic"]["lower_limit"],
            params["basic"]["upper_limit"],
            params["expert"]["p_interval"],
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

        dbh_value, tree_locations = dm.tree_locator(
            sections,
            X_c,
            Y_c,
            tree_vector,
            sector_perct,
            R,
            outliers,
            n_points_in,
            params["expert"]["point_threshold"],
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
        CCPluginFinProcessing.write_sf(cloud, dbh_value.reshape(-1), "dbh")
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


def _create_app_and_run(plugin_functor: CCPluginFinProcessing):
    """Encapsulate the 3DFin application and its the HiDPI support fix
    This way all could be run in a dedicated thread with pycc.RunInThread

    Parameters:
        plugin_functor (CCPluginFinProcessing): the functor you want to run
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
    import platform

    awareness_code = ctypes.c_int()
    if platform.system() == "Windows" and (
        platform.release() == "10" or platform.release() == "11"
    ):
        ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness_code))
        if awareness_code.value > 0:
            ctypes.windll.user32.SetThreadDpiAwarenessContext(
                ctypes.wintypes.HANDLE(-1)
            )
    fin_app = Application(plugin_functor)
    fin_app.run()


def main_cloudcompare():
    cc = pycc.GetInstance()

    entities = cc.getSelectedEntities()
    print(f"Selected entities: {entities}")

    if not entities or len(entities) > 1:
        raise RuntimeError("Please select one point cloud")

    point_cloud = entities[0]

    if not isinstance(point_cloud, pycc.ccPointCloud):
        raise RuntimeError("Selected entity should be a point cloud")

    z0_name = point_cloud.getCurrentDisplayedScalarField().getName()
    # TODO: if no scalar is selected we should handle this in the GUI and force the computation of
    # the height normalization

    # TODO: detect if a user already have computed something on this cloud (based on scalar field and entities in the DBTree)
    # and propose to force recompute (erase) or suggest to duplicate the point cloud.

    # TODO: Handle big coodinates (could be tested by maybe wait for CC API update)

    plugin_functor = CCPluginFinProcessing(cc, point_cloud, z0_name)

    cc.freezeUI(True)
    #TODO: catch exceptions into modals.
    pycc.RunInThread(_create_app_and_run, plugin_functor)
    cc.freezeUI(False)
    cc.updateUI()
