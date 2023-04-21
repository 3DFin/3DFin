import argparse
import configparser
import os
import timeit
from pathlib import Path
from typing import Any

import dendromatics as dm
import laspy
import numpy as np
import pandas as pd

from three_d_fin import __about__
from three_d_fin.gui.layout import Application


def fin_callback(params: dict):
    """3DFIN main algorithm.

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
    Filenames are: [original file name] + [specific suffix] + [.txt or .las]

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
    """
    # -------------------------------------------------------------------------------------------------
    # NON MODIFIABLE. These parameters should never be modified by the user.
    # -------------------------------------------------------------------------------------------------

    X_field = 0  # Which column contains X field  - NON MODIFIABLE
    Y_field = 1  # Which column contains Y field  - NON MODIFIABLE
    Z_field = 2  # Which column contains Z field  - NON MODIFIABLE

    # Z0_field = 3  # Which column contains Z0 field  - Unused - NON MODIFIABLE
    # tree_id_field = 4  # Which column contains tree ID field  - Unused - NON MODIFIABLE
    n_digits = 5  # Number of digits for voxel encoding.

    filename_las = params["misc"]["input_las"]
    basename_las = Path(params["misc"]["input_las"]).stem
    basepath_output = str(Path(params["misc"]["output_dir"]) / Path(basename_las))
    print(basepath_output)

    t_t = timeit.default_timer()

    if params["misc"]["is_normalized"]:
        # Read .LAS file.
        entr = laspy.read(filename_las)
        coords = np.vstack(
            (entr.x, entr.y, entr.z, entr[params["basic"]["z0_name"]])
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
            # Extracting ground points and DTM
            cloth_nodes = dm.generate_dtm(
                coords, cloth_resolution=params["expert"]["res_cloth"]
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

        las_dtm_points.write(filename_las + "_dtm_points.las")

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

    if params["misc"]["is_noisy"]:
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
        (assigned_cloud[:, 5] < params["advanced"]["stem_search_diameter"])
        & (assigned_cloud[:, 3] > params["advanced"]["minimum_height"])
        & (
            assigned_cloud[:, 3]
            < params["advanced"]["maximum_height"] + params["advanced"]["section_wid"]
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
        params["expert"]["minimum_diameter"],
        params["advanced"]["maximum_diameter"],
        params["expert"]["point_threshold"],
        params["expert"]["number_sectors"],
        params["expert"]["m_number_sectors"],
        params["expert"]["circa_points"],
    )

    dm.draw_axes(
        tree_vector,
        basepath_output + "_axes.las",
        params["expert"]["axis_downstep"],
        params["expert"]["axis_upstep"],
        params["basic"]["lower_limit"],
        params["basic"]["upper_limit"],
        params["expert"]["p_interval"],
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
        params["expert"]["point_threshold"],
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

    # matrix with tree height, DBH and (x,y) coordinates of each tree
    dbh_and_heights = np.zeros((dbh_values.shape[0], 4))

    if tree_heights.shape[0] != dbh_values.shape[0]:
        tree_heights = tree_heights[0 : dbh_values.shape[0], :]

    dbh_and_heights[:, 0] = tree_heights[:, 3]
    dbh_and_heights[:, 1] = dbh_values[:, 0]
    dbh_and_heights[:, 2] = tree_locations[:, 0]
    dbh_and_heights[:, 3] = tree_locations[:, 1]

    if not params["misc"]["txt"]:
        # Generating aggregated quality value for each section
        quality = np.zeros(sector_perct.shape)
        # Section does not pass quality check if:
        mask = (
            (
                sector_perct
                < params["expert"]["m_number_sectors"]
                / params["expert"]["number_sectors"]
                * 100
            )  # Percentange of occupied sectors less than minimum
            | (n_points_in > params["expert"]["point_threshold"])
            | (outliers > 0.3)  # Outlier probability larger than 30 %
            | (
                R < params["expert"]["minimum_diameter"]
            )  # Radius smaller than the minimum radius
            | (
                R > params["advanced"]["maximum_diameter"]
            )  # Radius larger than the maximum radius
        )
        # 0: does not pass quality check - 1: passes quality checks
        quality = np.where(mask, quality, 1)

        # Function to convert data to pandas DataFrames
        def to_pandas(data):
            # Covers np.arrays of shape == 2 (almost every case)
            if len(data.shape) == 2:
                df = pd.DataFrame(
                    data=data,
                    index=["T" + str(i + 1) for i in range(data.shape[0])],
                    columns=["S" + str(i + 1) for i in range(data.shape[1])],
                )

            # Covers np.arrays of shape == 1 (basically, data regarding the normalized height of every section).
            if len(data.shape) == 1:
                df = pd.DataFrame(data=data).transpose()
                df.index = ["Z0"]
                df.columns = ["S" + str(i + 1) for i in range(data.shape[0])]

            return df

        # Converting data to pandas DataFrames for ease to output them as excel files.
        df_diameters = to_pandas(R) * 2
        df_X_c = to_pandas(X_c)
        df_Y_c = to_pandas(Y_c)
        df_sections = to_pandas(sections)
        df_quality = to_pandas(quality)
        df_outliers = to_pandas(outliers)
        df_sector_perct = to_pandas(sector_perct)
        df_n_points_in = to_pandas(n_points_in)

        df_dbh_and_heights = pd.DataFrame(
            data=dbh_and_heights,
            index=["T" + str(i + 1) for i in range(dbh_values.shape[0])],
            columns=["TH", "DBH", "X", "Y"],
        )

        # Description to be added to each excel sheet.
        info_diameters = """Diameter of every section (S) of every tree (T).
            Units are meters.
            """
        info_X_c = (
            """(x) coordinate of the centre of every section (S) of every tree (T)."""
        )
        info_Y_c = (
            """(y) coordinate of the centre of every section (S) of every tree (T)."""
        )
        info_sections = """Normalized height (Z0) of every section (S).
        Units are meters."""
        info_quality = """Overal quality of every section (S) of every tree (T).
        0: Section does not pass quality checks - 1: Section passes quality checks.
        """
        info_outliers = """'Outlier probability' of every section (S) of every tree (T).
        It takes values between 0 and 1.
        """
        info_sector_perct = """Percentage of occupied sectors of every section (S) of every tree (T).
        It takes values between 0 and 100.
        """
        info_n_points_in = """Number of points in the inner circle of every section (S) of every tree (T).
        The lowest, the better.
        """
        info_dbh_and_heights = """Total height (TH) of each tree (T).
        Diameter at breast height (DBH) of each tree (T).
        (x, y) coordinates (X and Y) of each tree (T).
        """
        info_cloud_size = f"This cloud has {cloud_size} millions points and its area is {cloud_shape} km2"

        # Converting descriptions to pandas DataFrames for ease to include them in the excel file.
        df_info_diameters = pd.Series(info_diameters)
        df_info_X_c = pd.Series(info_X_c)
        df_info_Y_c = pd.Series(info_Y_c)
        df_info_sections = pd.Series(info_sections)
        df_info_quality = pd.Series(info_quality)
        df_info_outliers = pd.Series(info_outliers)
        df_info_sector_perct = pd.Series(info_sector_perct)
        df_info_n_points_in = pd.Series(info_n_points_in)
        df_info_dbh_and_heights = pd.Series(info_dbh_and_heights)
        df_info_cloud_size = pd.Series(info_cloud_size)

        xls_filename = basepath_output + ".xlsx"

        # Creating an instance of a excel writer
        writer = pd.ExcelWriter(xls_filename, engine="xlsxwriter")

        # Writing the descriptions

        df_info_dbh_and_heights.to_excel(
            writer,
            sheet_name="Plot Metrics",
            header=False,
            index=False,
            merge_cells=False,
        )

        df_info_cloud_size.to_excel(
            writer,
            sheet_name="Plot Metrics",
            startrow=1,
            header=False,
            index=False,
            merge_cells=False,
        )

        df_info_diameters.to_excel(
            writer, sheet_name="Diameters", header=False, index=False, merge_cells=False
        )

        df_info_X_c.to_excel(
            writer, sheet_name="X", header=False, index=False, merge_cells=False
        )

        df_info_Y_c.to_excel(
            writer, sheet_name="Y", header=False, index=False, merge_cells=False
        )

        df_info_sections.to_excel(
            writer, sheet_name="Sections", header=False, index=False, merge_cells=False
        )

        df_info_quality.to_excel(
            writer,
            sheet_name="Q(Overall Quality 0-1)",
            header=False,
            index=False,
            merge_cells=False,
        )

        df_info_outliers.to_excel(
            writer,
            sheet_name="Q1(Outlier Probability)",
            header=False,
            index=False,
            merge_cells=False,
        )

        df_info_sector_perct.to_excel(
            writer,
            sheet_name="Q2(Sector Occupancy)",
            header=False,
            index=False,
            merge_cells=False,
        )

        df_info_n_points_in.to_excel(
            writer,
            sheet_name="Q3(Points Inner Circle)",
            header=False,
            index=False,
            merge_cells=False,
        )

        # Writing the data
        df_dbh_and_heights.to_excel(
            writer, sheet_name="Plot Metrics", startrow=2, startcol=1
        )
        df_diameters.to_excel(writer, sheet_name="Diameters", startrow=2, startcol=1)
        df_X_c.to_excel(writer, sheet_name="X", startrow=2, startcol=1)
        df_Y_c.to_excel(writer, sheet_name="Y", startrow=2, startcol=1)
        df_sections.to_excel(writer, sheet_name="Sections", startrow=2, startcol=1)
        df_quality.to_excel(
            writer, sheet_name="Q(Overall Quality 0-1)", startrow=2, startcol=1
        )
        df_outliers.to_excel(
            writer, sheet_name="Q1(Outlier Probability)", startrow=2, startcol=1
        )
        df_sector_perct.to_excel(
            writer, sheet_name="Q2(Sector Occupancy)", startrow=2, startcol=1
        )
        df_n_points_in.to_excel(
            writer, sheet_name="Q3(Points Inner Circle)", startrow=2, startcol=1
        )

        writer.close()

    else:
        np.savetxt(basepath_output + "_diameters.txt", R * 2, fmt=("%.3f"))
        np.savetxt(basepath_output + "_X_c.txt", X_c, fmt=("%.3f"))
        np.savetxt(basepath_output + "_Y_c.txt", Y_c, fmt=("%.3f"))
        np.savetxt(basepath_output + "_check_circle.txt", check_circle, fmt=("%.3f"))
        np.savetxt(basepath_output + "_n_points_in.txt", n_points_in, fmt=("%.3f"))
        np.savetxt(basepath_output + "_sector_perct.txt", sector_perct, fmt=("%.3f"))
        np.savetxt(basepath_output + "_outliers.txt", outliers, fmt=("%.3f"))
        np.savetxt(
            basepath_output + "_dbh_and_heights.txt", dbh_and_heights, fmt=("%.3f")
        )
        np.savetxt(
            basepath_output + "_sections.txt", np.column_stack(sections), fmt=("%.3f")
        )

    elapsed_las2 = timeit.default_timer() - t_las2
    print("Total time:", "   %.2f" % elapsed_las2, "s")

    elapsed_t = timeit.default_timer() - t_t

    # -------------------------------------------------------------------------------------------------------------
    print("---------------------------------------------")
    print("End of process!")
    print("---------------------------------------------")
    print("Total time:", "   %.2f" % elapsed_t, "s")
    print("nº of trees:", X_c.shape[0])


def _validate_config(config: configparser.ConfigParser) -> dict[str, dict[str, Any]]:
    """Get parameters from config file return them organized in a dictionnary.

    Returns
    -------
    options : dict[str, dict[str, Any]]
        Dictionary of parameters. It is organised following the 3DFINconfig.ini file:
        Each parameters are sorted in sub-dict ("basic", "expert", "advanced").
        TODO: A "misc" subsection enclose all parameters needed by 3DFIN but not
        defined in the the config file.
        TODO: it is vendored from layout, we need a proper class to do validation
    """
    params: dict[str, dict[str, Any]] = {}
    params["misc"] = {}
    params["basic"] = {}
    params["expert"] = {}
    params["advanced"] = {}

    # -------------------------------------------------------------------------------------------------
    # BASIC PARAMETERS. These are the parameters to be checked (and changed if needed) for each dataset/plot
    # All parameters are in m or points
    # -------------------------------------------------------------------------------------------------

    params["basic"]["z0_name"] = config.get(
        "basic", "z0_name"
    )  # Name of the Z0 field in the LAS file containing the cloud.
    # If the normalized heights are stored in the Z coordinate of the .LAS file: field_name_z0 = "z" (lowercase)

    # Upper and lower limits (vertical) of the stripe where it should be reasonable to find stems with minimum presence of shrubs or branches.
    params["basic"]["upper_limit"] = float(
        config.get("basic", "upper_limit")
    )  # Values, normally between 2 and 5
    params["basic"]["lower_limit"] = float(
        config.get("basic", "lower_limit")
    )  # Values, normally between 0.3 and 1.3

    params["basic"]["number_of_iterations"] = int(
        config.get("basic", "number_of_iterations")
    )  # Number of iterations of 'peeling off branches'.
    # Values between 0 (no branch peeling/cleaning) and 5 (very extreme branch peeling/cleaning)

    # -------------------------------------------------------------------------------------------------
    # Advanced PARAMETERS. They should only be modified when no good results are obtained tweaking basic parameters.
    # They require a deeper knowledge of how the algorithm and the implementation work
    # -------------------------------------------------------------------------------------------------

    params["advanced"]["stem_search_diameter"] = (
        float(config.get("advanced", "stem_search_diameter")) / 2
    )  # Points within this distance from tree axes will be considered as potential stem points.
    # Values between maximum diameter and 1 (exceptionally greater than 1: very large diameters and/or intricate stems)

    params["advanced"]["maximum_diameter"] = (
        float(config.get("advanced", "maximum_diameter")) / 2
    )  # Maximum radius expected for any section during circle fitting.

    params["advanced"]["minimum_height"] = float(
        config.get("advanced", "minimum_height")
    )  # Lowest height
    params["advanced"]["maximum_height"] = float(
        config.get("advanced", "maximum_height")
    )  # highest height

    params["advanced"]["section_len"] = float(
        config.get("advanced", "section_len")
    )  # sections are this long (z length)
    params["advanced"]["section_wid"] = float(
        config.get("advanced", "section_wid")
    )  # sections are this wide

    # -------------------------------------------------------------------------------------------------
    # EXPERT PARAMETERS. They should only be modified when no good results are obtained peaking basic parameters.
    # They require a deeper knowledge of how the algorithm and the implementation work
    # *Stored in the main script in this version.
    # -------------------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------------------
    # Stem identification within the stripe
    # -------------------------------------------------------------------------------------------------
    params["expert"]["res_xy_stripe"] = float(
        config.get("expert", "res_xy_stripe")
    )  # (x, y)voxel resolution during stem identification
    params["expert"]["res_z_stripe"] = float(
        config.get("expert", "res_z_stripe")
    )  # (z) voxel resolution during stem identification

    params["expert"]["number_of_points"] = int(
        config.get("expert", "number_of_points")
    )  # minimum number of points per stem within the stripe (DBSCAN clustering).
    # Values, normally between 500 and 3000

    params["expert"]["verticality_scale_stripe"] = float(
        config.get("expert", "verticality_scale_stripe")
    )  # Vicinity radius for PCA during stem extraction
    params["expert"]["verticality_thresh_stripe"] = float(
        config.get("expert", "verticality_thresh_stripe")
    )  # Verticality threshold durig stem extraction

    # -------------------------------------------------------------------------------------------------
    # Tree individualization.
    # -------------------------------------------------------------------------------------------------
    params["expert"]["res_xy"] = float(
        config.get("expert", "res_xy")
    )  # (x, y) voxel resolution during tree individualization
    params["expert"]["res_z"] = float(
        config.get("expert", "res_z")
    )  # (z) voxel resolution during tree individualization

    params["expert"]["minimum_points"] = int(
        config.get("expert", "minimum_points")
    )  # Minimum number of points within a stripe to consider it as a potential tree during tree individualization

    params["expert"]["verticality_scale_stems"] = float(
        config.get("expert", "verticality_scale_stems")
    )  # DBSCAN minimum number of points during stem identification
    params["expert"]["verticality_thresh_stems"] = float(
        config.get("expert", "verticality_thresh_stems")
    )  # Verticality threshold durig stem identification

    params["expert"]["height_range"] = float(
        config.get("expert", "height_range")
    )  # only stems where points extend vertically throughout this range are considered.
    params["expert"]["maximum_d"] = float(
        config.get("expert", "maximum_d")
    )  # Points that are closer than d_max to an axis are assigned to that axis during individualize_trees process.

    params["expert"]["distance_to_axis"] = float(
        config.get("expert", "distance_to_axis")
    )  # Points within this distance from tree axes will be used to find tree height
    params["expert"]["res_heights"] = float(
        config.get("expert", "res_heights")
    )  # Resolution for the voxelization while computing tree heights
    params["expert"]["maximum_dev"] = float(
        config.get("expert", "maximum_dev")
    )  # Maximum degree of vertical deviation from the axis

    # -------------------------------------------------------------------------------------------------
    # Extracting sections.
    # -------------------------------------------------------------------------------------------------
    params["expert"]["number_points_section"] = int(
        config.get("expert", "number_points_section")
    )  # Minimum number of points in a section to be considered
    params["expert"]["diameter_proportion"] = float(
        config.get("expert", "diameter_proportion")
    )  # Proportion, regarding the circumference fit by fit_circle, that the inner circumference radius will have as length
    params["expert"]["minimum_diameter"] = (
        float(config.get("expert", "minimum_diameter")) / 2
    )  # Minimum radius expected for any section circle fitting.
    params["expert"]["point_threshold"] = int(
        config.get("expert", "point_threshold")
    )  # Number of points inside the inner circle
    params["expert"]["point_distance"] = float(
        config.get("expert", "point_distance")
    )  # Maximum distance among points to be considered within the same cluster.
    params["expert"]["number_sectors"] = int(
        config.get("expert", "number_sectors")
    )  # Number of sectors in which the circumference will be divided
    params["expert"]["m_number_sectors"] = int(
        config.get("expert", "m_number_sectors")
    )  # Minimum number of sectors that must be occupied.
    params["expert"]["circle_width"] = float(
        config.get("expert", "circle_width")
    )  # Width, in centimeters, around the circumference to look for points

    # -------------------------------------------------------------------------------------------------
    # Drawing circles.
    # -------------------------------------------------------------------------------------------------
    params["expert"]["circa_points"] = int(config.get("expert", "circa"))

    # -------------------------------------------------------------------------------------------------
    # Drawing axes.
    # -------------------------------------------------------------------------------------------------
    params["expert"]["p_interval"] = float(config.get("expert", "p_interval"))
    params["expert"]["axis_downstep"] = float(config.get("expert", "axis_downstep"))
    params["expert"]["axis_upstep"] = float(
        config.get("expert", "axis_upstep")
    )  # From the stripe centroid, how much (upwards direction) will the drawn axes extend.

    # -------------------------------------------------------------------------------------------------
    # Height normalization
    # -------------------------------------------------------------------------------------------------
    params["expert"]["res_ground"] = float(config.get("expert", "res_ground"))
    params["expert"]["min_points_ground"] = int(
        config.get("expert", "min_points_ground")
    )
    params["expert"]["res_cloth"] = float(config.get("expert", "res_cloth"))

    return params


def launch_application() -> int:
    """Parse the command line and launch the GUI or the CLI application.

    Main entry point for the 3DFin application:
        - Launch the GUI if the command is called without aguments.

        - Launch the CLI by appending the 'cli' subcommand to the command. For other
          arguments, the reader should return to the body of the function.

    Returns
    -------
    exit_code : int
        POSIX minimal exit_code (0 = SUCCESS, 1 = ERROR)
    """
    EXIT_ERROR = 1
    EXIT_SUCCESS = 0

    parser = argparse.ArgumentParser(
        prog=f"3DFin",
        description=f"""
        {__about__.__copyright_info_1__}
        {__about__.__copyright_info_2__}
        {__about__.__license_msg__}
        """,   
    )
    parser.add_argument("--version", '-v', action="version", version=__about__.__version__)

    # Create a subparser for cli subcommand
    subparsers = parser.add_subparsers(dest="subcommand")
    cli_subparser = subparsers.add_parser(
        "cli", help="launch the app in command line mode"
    )
    cli_subparser.add_argument("input_file", help="Las or Laz input file")
    cli_subparser.add_argument(
        "output_directory", help="output directory where to put the results"
    )
    cli_subparser.add_argument("params_file", help=".ini files with parameters")
    cli_subparser.add_argument(
        "--export_txt",
        action="store_true",
        help="Export tabular data in ASCII CSV files instead of XLSX",
    )
    cli_subparser.add_argument(
        "--normalize", action="store_true", help="Normalize the data with CSF algorithm"
    )
    cli_subparser.add_argument(
        "--denoise",
        action="store_true",
        help="Denoise the data, if outliers below ground level are expected",
    )
    cli_subparser.add_argument("--version", '-v', action="version", version=__about__.__version__)

    cli_parse = parser.parse_args()

    print(__about__.__copyright_info_1__)
    print(__about__.__copyright_info_2__)
    print(__about__.__license_msg__)
    # No subcommand, launch GUI
    if cli_parse.subcommand is None:

        fin_app = Application(fin_callback)
        _ = fin_app.run()
        # TODO it's always sucess for now but we should do exception handling
        return EXIT_SUCCESS

    # Else, the CLI case
    # First, read the param file and sanitize the input
    config_path = Path(cli_parse.params_file)
    if not config_path.exists() or not config_path.is_file():
        print("Parameters: File does not exist")
        return EXIT_ERROR

    with config_path.open("r") as f:
        params = configparser.ConfigParser()
        try:
            params.read_file(f)
        except configparser.ParsingError:
            print("Parameters: invalid .ini file")
            return EXIT_ERROR

    try:
        # TODO: We should have a validation class here
        valid_params = _validate_config(params)
    except configparser.NoOptionError as error:
        print(
            f"Parameters: invalid option '{error.option}' in section '{error.section}'"
        )
        return EXIT_ERROR
    except ValueError as error:
        print(f"Parameters: {error.args[0]}")
        return EXIT_ERROR

    # Second, We check las file validity
    input_las = Path(cli_parse.input_file)
    if not input_las.exists() or not input_las.is_file():
        print("Input file: file does not exists")
        return EXIT_ERROR
    try:
        laspy.open(input_las, read_evlrs=False)
    except laspy.LaspyException:
        print("Input file: invalid las file")
        return EXIT_ERROR

    # At last, We check the validity of the current output directory
    output_dir = Path(cli_parse.output_directory)
    if (
        not output_dir.exists()
        or not output_dir.is_dir()
        or not os.access(
            output_dir, os.W_OK
        )  # os.access won't work very well on Windows, we may still have to mess with exceptions
    ):
        print("Invalid output directory")
        return EXIT_ERROR

    # Wrap all in the misc section
    valid_params["misc"]["is_normalized"] = not cli_parse.normalize
    valid_params["misc"]["is_noisy"] = cli_parse.denoise
    valid_params["misc"]["txt"] = cli_parse.export_txt
    valid_params["misc"]["input_las"] = cli_parse.input_file
    valid_params["misc"]["output_dir"] = cli_parse.output_directory

    # Run processing
    fin_callback(valid_params)
    # TODO it's always sucess for now but we should do exception handling
    return EXIT_SUCCESS
