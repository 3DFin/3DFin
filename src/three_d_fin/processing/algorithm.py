import timeit
from pathlib import Path

import dendromatics as dm
import laspy
import numpy as np

from three_d_fin.processing.configuration import FinConfiguration
from three_d_fin.processing.io import export_tabular_data


def fin_callback(config: FinConfiguration):
    """3DFin main algorithm.

    -----------------------------------------------------------------------------
    ------------------        General Description          ----------------------
    -----------------------------------------------------------------------------

    This Python script implements an algorithm to detect the trees present
    in a ground-based 3D point cloud from a forest plot,
    and compute individual tree parameters: tree height, tree location,
    diameters along the stem (including DBH), and stem axis.

    The input point cloud will be in .LAS/.LAZ format and can contain extra fields (.LAS standard or not)
    This algorithm is mainly based on rules, although it uses clusterization in some stages.
    Also, the input point cloud can come from terrestrail photogrammetry, TLS or mobile (e.g. hand-held) LS,
    a combination of those, and/or a combination of those with UAV-(LS or SfM), or ALS.

    The algorithm may be divided in three main steps:

        1.	Identification of stems in an user-defined horizontal stripe.
        2.	Tree individualization based on point-to-stem-axis distances.
        3.	Robust computation of stem diameter at different section heights.

    -----------------------------------------------------------------------------
    ------------------   Heights in the input .LAS file    ----------------------
    -----------------------------------------------------------------------------

    This script uses Z and Z0 to describe coordinates referring to 'heights'.
        - Z refers to the originally captured elevation in the point cloud
        - Z0 refers to a normalized height (elevation from the ground).
    This script needs normalized heights to work, but also admits elevation
    coordinates and preserves them in the outputs, as additional information
    Then, the input point cloud might include just just Z0, or both Z and Z0.

    Before running script, it should be checked where are the normalized heights stored in the input file: 'z' or another field.
    The name of that field is one of the basic input parameters:
        - field_name_z0: Name of the field containing the height normalized data in the .LAS file.
    If the normalized heights are stored in the z coordinate of the .LAS file, the value of field_name_z0 will be 'z' (lowercase).

    -----------------------------------------------------------------------------
    ------------------                Outputs              ----------------------
    -----------------------------------------------------------------------------

    After all computations are complete, the following files are output:
    Filenames are: [original file name] + [specific suffix] + [.txt, .las or .ini]

    LAS files (mainly for checking visually the outputs).
    They can be open straightaway in CloudCompare, where 'colour visualization' of fields with additional information is straightforward

    •	[original file name]_tree_ID_dist_axes: LAS file containing the original point cloud and a scalar field that contains tree IDs.
    •	[original file name]_axes: LAS file containing stem axes coordinates.
    •	[original file name]_circ: LAS file containing circles (sections) coordinates.
    •	[original file name]_stripe: LAS file containing the stems obtained from the stripe during step 1.
    •	[original file name]_tree_locator: LAS file containing the tree locators coordinates.
    •	[original file name]_tree_heights: LAS file containing the highest point from each tree.

    Text files with tabular data:
        Files contain TAB-separated information with as many rows as trees detected in the plot and as many columns as stem sections considered
        All units are m or points.
        _outliers and _check_circle have no units

    •	[original file name]_dbh_and_heights: Text file containing tree height, tree location and DBH of every tree as tabular data.
    •	[original file name]_X_c: Text file containing the (x) coordinate of the centre of every section of every tree as tabular data.
    •	[original file name]_Y_c: Text file containing the (y) coordinate of the centre of every section of every tree as tabular data.
    •	[original file name]_diameters: Text file containing the diameter of every section of every tree as tabular data.
    •	[original file name]_outliers: Text file containing the 'outlier probability' of every section of every tree as tabular data.
    •	[original file name]_sector_perct: Text file containing the sector occupancy of every section of every tree as tabular data.
    •	[original file name]_check_circle: Text file containing the 'check' status of every section of every tree as tabular data.
    •	[original file name]_n_points_in: Text file containing the number of points within the inner circle of every section of every tree as tabular data.
    •	[original file name]_sections: Text file containing the sections as a vector.

    •	[original file name]_sections: ASCII file containing the configuration used for the run.
    """
    # -------------------------------------------------------------------------------------------------
    # NON MODIFIABLE. These parameters should never be modified by the user.
    # -------------------------------------------------------------------------------------------------

    X_field = 0  # Which column contains X field  - NON MODIFIABLE
    Y_field = 1  # Which column contains Y field  - NON MODIFIABLE
    Z_field = 2  # Which column contains Z field  - NON MODIFIABLE
    n_digits = 5  # Number of digits for voxel encoding.

    filename_las = str(config.misc.input_file.resolve())
    basename_las = Path(config.misc.input_file).stem
    basepath_output = str(Path(config.misc.output_dir) / Path(basename_las))
    print(basepath_output)

    t_t = timeit.default_timer()

    if config.misc.is_normalized:
        # Read .LAS file.
        entr = laspy.read(filename_las)
        coords = np.vstack(
            (entr.x, entr.y, entr.z, entr[config.basic.z0_name])
        ).transpose()

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
        entr = laspy.read(filename_las)
        coords = np.vstack((entr.x, entr.y, entr.z)).transpose()

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
            # Extracting ground points and DTM
            cloth_nodes = dm.generate_dtm(
                coords, cloth_resolution=config.expert.res_cloth
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
        las_dtm_points = laspy.create(point_format=2, file_version="1.2")
        las_dtm_points.x = dtm[:, 0]
        las_dtm_points.y = dtm[:, 1]
        las_dtm_points.z = dtm[:, 2]

        las_dtm_points.write(basepath_output + "_dtm_points.las")

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
    t_las = timeit.default_timer()
    las_stripe = laspy.create(point_format=2, file_version="1.2")
    las_stripe.x = clust_stripe[:, X_field]
    las_stripe.y = clust_stripe[:, Y_field]
    las_stripe.z = clust_stripe[:, Z_field]

    las_stripe.add_extra_dim(laspy.ExtraBytesParams(name="tree_ID", type=np.int32))
    las_stripe.tree_ID = clust_stripe[:, -1]
    las_stripe.write(basepath_output + "_stripe.las")

    # Whole cloud including new fields
    entr.add_extra_dim(laspy.ExtraBytesParams(name="dist_axes", type=np.float64))
    entr.add_extra_dim(laspy.ExtraBytesParams(name="tree_ID", type=np.int32))
    entr.dist_axes = assigned_cloud[:, 5]
    entr.tree_ID = assigned_cloud[:, 4]

    if config.misc.is_noisy:
        entr.add_extra_dim(laspy.ExtraBytesParams(name="Z0", type=np.float64))
        entr.Z0 = z0_values
    entr.write(basepath_output + "_tree_ID_dist_axes.las")
    elapsed_las = timeit.default_timer() - t_las
    print("Total time:", "   %.2f" % elapsed_las, "s")

    # Tree heights
    las_tree_heights = laspy.create(point_format=2, file_version="1.2")
    las_tree_heights.x = tree_heights[:, 0]  # x
    las_tree_heights.y = tree_heights[:, 1]  # y
    las_tree_heights.z = tree_heights[:, 2]  # z
    las_tree_heights.add_extra_dim(laspy.ExtraBytesParams(name="z0", type=np.float64))
    las_tree_heights.z0 = tree_heights[:, 3]  # z0
    las_tree_heights.add_extra_dim(
        laspy.ExtraBytesParams(name="deviated", type=np.int32)
    )
    las_tree_heights.deviated = tree_heights[
        :, 4
    ]  # vertical deviation binary indicator
    las_tree_heights.write(basepath_output + "_tree_heights.las")

    # stem extraction and curation
    print("---------------------------------------------")
    print("4.-Extracting and curating stems...")
    print("---------------------------------------------")

    xyz0_coords = assigned_cloud[
        (assigned_cloud[:, 5] < (config.advanced.stem_search_diameter) / 2.0)
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
        config.expert.minimum_diameter / 2.0,
        config.advanced.maximum_diameter / 2.0,
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

    coords = dm.draw_circles(
        X_c,
        Y_c,
        R,
        sections,
        check_circle,
        sector_perct,
        n_points_in,
        tree_vector,
        outliers,
        basepath_output + "_circ.las",
        config.expert.minimum_diameter / 2.0,
        config.advanced.maximum_diameter / 2.0,
        config.expert.point_threshold,
        config.expert.number_sectors,
        config.expert.m_number_sectors,
        config.expert.circa,
    )

    dm.draw_axes(
        tree_vector,
        basepath_output + "_axes.las",
        config.expert.axis_downstep,
        config.expert.axis_upstep,
        config.basic.lower_limit,
        config.basic.upper_limit,
        config.expert.p_interval,
    )

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

    las_tree_locations = laspy.create(point_format=2, file_version="1.2")
    las_tree_locations.x = tree_locations[:, 0]
    las_tree_locations.y = tree_locations[:, 1]
    las_tree_locations.z = tree_locations[:, 2]
    las_tree_locations.add_extra_dim(
        laspy.ExtraBytesParams(name="diameters", type=np.float64)
    )
    las_tree_locations.diameters = dbh_values[:, 0]

    las_tree_locations.write(basepath_output + "_tree_locator.las")

    # -------------------------------------------------------------------------------------------------------------
    # Exporting results
    # -------------------------------------------------------------------------------------------------------------
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