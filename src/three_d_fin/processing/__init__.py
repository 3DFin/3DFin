import argparse
import configparser
import os
from pathlib import Path
from typing import Any

import laspy

from three_d_fin import __about__
from three_d_fin.gui.layout import Application
from three_d_fin.processing import algorithm


def launch_application() -> int:
    """Parse the command line and launch the GUI or the CLI application.

    Main entry point for the 3DFin application:
        - Launch the GUI if the command is called without aguments.

        - Launch the CLI by appending the 'cli' subcommand to the command. For other
          arguments, the reader should return to the body of the function.

    Returns
    -------
    exit_code : int
        POSIX minimal exit code (0 = SUCCESS, 1 = ERROR)
    """
    EXIT_ERROR = 1
    EXIT_SUCCESS = 0

    parser = argparse.ArgumentParser(
        prog="3DFin",
        description=f"""
            {__about__.__copyright_info_1__}
            {__about__.__copyright_info_2__}
            {__about__.__license_msg__}""",
    )
    parser.add_argument(
        "--version", "-v", action="version", version=__about__.__version__
    )

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
    cli_subparser.add_argument(
        "--version", "-v", action="version", version=__about__.__version__
    )

    cli_parse = parser.parse_args()

    print(__about__.__copyright_info_1__)
    print(__about__.__copyright_info_2__)
    print(__about__.__license_msg__)
    # No subcommand, launch GUI
    if cli_parse.subcommand is None:
        fin_app = Application(algorithm.fin_callback)
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
    algorithm.fin_callback(valid_params)
    # TODO it's always sucess for now but we should do exception handling
    return EXIT_SUCCESS


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
