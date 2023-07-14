import timeit
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Tuple

import dendromatics as dm
import numpy as np

from three_d_fin.processing.configuration import FinConfiguration
from three_d_fin.processing.io import export_tabular_data
from three_d_fin.processing.progress import Progress


class FinProcessing(ABC):
    """Define the 3DFin algorithm and its I/O requirements.

    See the process(...) method for full description of the algorithmic aspects.
    I/O are defined as abstract methods that must be overridden by implementers.
    """

    progress: Progress = Progress()

    config: FinConfiguration

    base_cloud: Any

    output_basepath: Path

    overwrite: bool = False

    def __init__(self, config: FinConfiguration) -> None:
        """Init the FinProcessing object.

        Parameters
        ----------
        config : FinConfiguration
            Self explanatory, the 3DFin configuration.
        """
        self.set_config(config)

    def set_config(self, config: FinConfiguration) -> None:
        """Set the configuration.

        It's basically equivalent to the creation of a new object.

        Parameters
        ----------
        config : FinConfiguration
            Self explanatory, the 3DFin configuration.
        """
        self.config = config
        self._construct_output_path()

    def check_already_computed_data(self) -> bool:
        """Check if the processing output could collides with other files.

        Returns
        -------
        previous_data : bool
            True if the algorithm output could be in competition with data from
            a previous computation, False otherwise. Default implementation always
            return False.
        """
        any_of = False
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
        return any_of

    @abstractmethod
    def _construct_output_path(self) -> None:
        """Construct the ouput path for the algorithm output.

        It is used to construct the output_basepath attibute.
        """
        pass

    @abstractmethod
    def _pre_processing_hook(self) -> None:
        """Execute instructions before the main algorithm.

        Implementers could either use this hook or the constructor to
        introduce pre processing steps.
        """
        pass

    @abstractmethod
    def _post_processing_hook(self) -> None:
        """Execute instructions to run after the main algorithm."""
        pass

    @abstractmethod
    def _load_base_cloud(self) -> None:
        """Load the base cloud from a provider.

        The base cloud is the point cloud from which the algoritm will run.
        It is used to set the base_cloud attribute. It could also could be set
        from the constructor.
        """
        pass

    @abstractmethod
    def _get_xyz_z0_from_base(self) -> np.ndarray:
        """Extract the x, y, z and z0 coordinates from the base_cloud.

        Returns
        -------
        xyz_z0 : np.ndarray
            A numpy array of shape (n, 4) where n is the number of points in the
            cloud. (x), (y), (z) and Z0 coordinates are stored in the first, second,
            third and fourth columns respectively.
        """
        pass

    @abstractmethod
    def _get_xyz_from_base(self) -> np.ndarray:
        """Extract the x, y, z and z0 coordinates from the base_cloud.

        Returns
        -------
        xyz : np.ndarray
            A numpy array of shape (n, 3) where n is the number of points in the
            cloud. (x), (y), (z) coordinates are stored in the first, second,
            third columns respectively.
        """
        pass

    @abstractmethod
    def _export_dtm(self, dtm: np.ndarray):
        """Export the DTM.

        Parameters
        ----------
        dtm : np.ndarray
            A numpy array of shape (n, 3) where n is the number of points in the cloud.
            (x), (y) and (z) coordinates are stored in the first, second,
            third columns respectively.
        """
        pass

    @abstractmethod
    def _export_stripe(self, clust_stripe: np.ndarray):
        """Export the stem extracted from the stripe.

        Parameters
        ----------
        clust_stripe : np.ndarray
            A numpy array of shape (n, 4) where n is the number of points in the cloud.
            It consists of 4 columns: (x), (y) and (z) coordinates, and a 4th column containing
            the cluster_ID of the cluster that each point belongs to.
        """
        pass

    @abstractmethod
    def _enrich_base_cloud(self, assigned_cloud: np.ndarray):
        """Enrich the base cloud with the cluster ID and the z0 values and export it.

        Parameters
        ----------
        assigned_cloud : np.ndarray
            A numpy array of shape (n, 6) where n is the number of points in the cloud.
            It consists of 6 columns: (x), (y), (z) and z0 coordinates,
            5th column containing tree ID that each point belongs to and a 6th column containing
            point distance to closest axis.
        """
        pass

    @abstractmethod
    def _export_tree_height(self, tree_heights: np.ndarray):
        """Export the tree heights.

        Parameters
        ----------
        tree_heights : np.ndarray
            Matrix containing the heights of individualized trees.
            A numpy array of shape (n, 5) where n is the number of trees in the cloud.
            It consists of (x), (y), (z) and (z0) coordinates of the highest point of the tree
            and a 5th column containing a binary indicator:
            0 - tree was too deviated from vertical, and height may not be accurate,
            or 1 - tree was not too deviated from vertical, thus height may be trusted
        """
        pass

    @abstractmethod
    def _export_circles(self, circles_coords: np.ndarray):
        """Export the circles.

        Parameters
        ----------
        circles_coords : np.ndarray
            Matrix containing the coordinates of the circles and their associated
            meta data.
        """
        pass

    @abstractmethod
    def _export_axes(self, axes_points: np.ndarray, tilt: np.ndarray):
        """Export the axes.

        Parameters
        ----------
        axes_points : numpy.ndarray
            Matrix that describes the point cloud of the axes.
        tilt : numpy.ndarray
            Matrix that describes the tilt of each axes
        """
        pass

    @abstractmethod
    def _export_tree_locations(
        self, tree_locations: np.ndarray, dbh_values: np.ndarray
    ):
        """Export the tree locations.

        Parameters
        ----------
        tree_locations : np.ndarray
            A numpy array of shape (n, 3) where n is the number of trees in the cloud.
            It consists of (x), (y), (z) coordinates of the base
            of the tree.
        dbh_values : np.ndarray
            Matrix containing the DBH values of individualized trees.
        """
        pass

    def process(self):
        """3DFin main algorithm.

        -----------------------------------------------------------------------------
        ------------------        General Description          ----------------------
        -----------------------------------------------------------------------------

        This method implements an algorithm to detect the trees present
        in a ground-based 3D point cloud from a forest plot,
        and compute individual tree parameters: tree height, tree location,
        diameters along the stem (including DBH), and stem axis.

        This algorithm is mainly based on rules, although it uses clusterization
        in some stages.
        Also, the input point cloud can come from terrestrial photogrammetry,
        TLS or mobile (e.g. hand-held) LS, a combination of those, and/or
        a combination of those with UAV-(LS or SfM), or ALS.

        The algorithm may be divided in three main steps:

            1.	Identification of stems in an user-defined horizontal stripe.
            2.	Tree individualization based on point-to-stem-axis distances.
            3.	Robust computation of stem diameter at different section heights.

        -----------------------------------------------------------------------------
        ------------------        Heights in the input        -----------------------
        -----------------------------------------------------------------------------
        This algorithm needs normalized heights (z0) to work, but also admits
        elevation coordinates (z) and preserves them in the outputs, as additional
        information.

        In other words, it operates on numpy arrays of size (n, 4) where first
        three columns are (x), (y), (z) coordinates and fourth column is (z0).

        _get_xyz_z0_from_base(...) method is responsible for levraging field_name_z0
        parameters in order to provide the ad-hoc numpy array from the original point cloud.
        If the user want to use an unormalized point cloud _get_xyz_from_base(...)
        is responsible for feeding CSF algorithm with the original point cloud in order
        to compute a normalized point cloud.

        -----------------------------------------------------------------------------
        ------------------                Outputs              ----------------------
        -----------------------------------------------------------------------------

        After all computations are complete, the following files are output:
        Filenames are: [original file name] + [specific suffix] + [.txt, .xlsx, .ini]

        Tabular data:
            Files contain TAB-separated information with as many rows as trees detected
            in the plot and as many columns as stem sections considered.
            All units are m or points. _outliers and _check_circle have no units. the
            format of the tabular data is given by the export_txt parameter

        In xlsx format (export_txt == False):
        •   [original file name].xlsx

        Or in with .txt extension, in ASCII format (export_txt == True):
        •	[original file name]_dbh_and_heights: Text file containing tree height, tree location and DBH of every tree as tabular data.
        •	[original file name]_X_c: Text file containing the (x) coordinate of the centre of every section of every tree as tabular data.
        •	[original file name]_Y_c: Text file containing the (y) coordinate of the centre of every section of every tree as tabular data.
        •	[original file name]_diameters: Text file containing the diameter of every section of every tree as tabular data.
        •	[original file name]_outliers: Text file containing the 'outlier probability' of every section of every tree as tabular data.
        •	[original file name]_sector_perct: Text file containing the sector occupancy of every section of every tree as tabular data.
        •	[original file name]_check_circle: Text file containing the 'check' status of every section of every tree as tabular data.
        •	[original file name]_n_points_in: Text file containing the number of points within the inner circle of every section of every tree as tabular data.
        •	[original file name]_sections: Text file containing the sections as a vector.

        The configuration file (ini format):
        •	[original file name]_config.ini: ASCII file containing the configuration used for the run.

        The abstract methods of this class give the oportunity to the implementers to output some files or
        in memory data structures (depending on the execution contexts) at specific "steps" of the algorithm:
        •	_enrich_base_cloud(...) -> the original point cloud and a scalar field that contains tree IDs.
        •	_export_axes(...) -> the stem axes coordinates.
        •	_export_circles(...) -> the circles (sections) coordinates.
        •	_export_stripe(...) -> the stems obtained from the stripe during step 1.
        •	_export_tree_locations(...) -> the tree locators coordinates.
        •	_export_tree_height(...) -> the highest point from each tree.
        """
        if self.config is None:
            raise Exception("Please set configuration before running any processing")

        # -------------------------------------------------------------------------------------------------
        # NON MODIFIABLE. These parameters should never be modified by the user.
        # -------------------------------------------------------------------------------------------------
        X_field = 0  # Which column contains X field  - NON MODIFIABLE
        Y_field = 1  # Which column contains Y field  - NON MODIFIABLE
        Z_field = 2  # Which column contains Z field  - NON MODIFIABLE
        n_digits = 5  # Number of digits for voxel encoding.

        # Aliasing config
        config = self.config

        t_t = timeit.default_timer()

        # Load the base_cloud if needed
        self._load_base_cloud()

        def __cloud_size_analysis(coords: np.ndarray) -> Tuple[int, int]:
            """Analyze the size of the cloud.

            Given a point cloud, this private function voxelizes it and output
            a rough estimation of its extent and number of points.

            Parameters
            ----------
            coords : np.ndarray
                A numpy array of shape (n, m) where n is
                the number of points in the cloud and m is an arbitrary number of columns
                where m >= 3.

            Returns
            -------
            cloud_size : int
                Estimation of the number of points in the cloud.
            cloud_shape : int
                Estimated area / XY extent of the cloud.
            """
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
            return cloud_size, cloud_shape

        if config.misc.is_normalized:
            coords = self._get_xyz_z0_from_base()
            # Number of points and area occuped by the plot.
            cloud_size, cloud_shape = __cloud_size_analysis(coords)
            print("---------------------------------------------")
            print("Cloud is already normalized...")
            print("---------------------------------------------")

        else:
            coords = self._get_xyz_from_base()
            # Number of points and area occuped by the plot.
            cloud_size, cloud_shape = __cloud_size_analysis(coords)
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

            # Completing the DTM
            completed_dtm = dm.complete_dtm(dtm)

            # export DTM
            self._export_dtm(completed_dtm)

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
            progress_hook=self.progress.update,
        )

        print("  ")
        print("---------------------------------------------")
        print("3.-Exporting complete cloud and stripe...")
        print("---------------------------------------------")

        t_las = timeit.default_timer()
        # Export Stripe

        clean_stripe = clust_stripe[np.isin(clust_stripe[:, -1], tree_vector[:, 0])]

        self._export_stripe(clean_stripe)

        # Whole cloud including new
        self._enrich_base_cloud(assigned_cloud)

        elapsed_las = timeit.default_timer() - t_las
        print("Total time:", "   %.2f" % elapsed_las, "s")

        # Export tree heights
        self._export_tree_height(tree_heights)

        # stem extraction and curation
        print("---------------------------------------------")
        print("4.-Extracting and curating stems...")
        print("---------------------------------------------")

        xyz0_coords = assigned_cloud[
            (assigned_cloud[:, 5] < (config.advanced.stem_search_diameter / 2.0))
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
            progress_hook=self.progress.update,
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

        circles_coords = dm.generate_circles_cloud(
            X_c,
            Y_c,
            R,
            sections,
            check_circle,
            sector_perct,
            n_points_in,
            tree_vector,
            outliers,
            config.expert.minimum_diameter / 2.0,
            config.advanced.maximum_diameter / 2.0,
            config.expert.point_threshold,
            config.expert.number_sectors,
            config.expert.m_number_sectors,
            config.expert.circa,
        )

        # Export circles
        self._export_circles(circles_coords)

        axes, tilt = dm.generate_axis_cloud(
            tree_vector,
            config.expert.axis_downstep,
            config.expert.axis_upstep,
            config.basic.lower_limit,
            config.basic.upper_limit,
            config.expert.p_interval,
        )

        # Export axes
        self._export_axes(axes, tilt)

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

        # Export tree locations
        self._export_tree_locations(tree_locations, dbh_values)

        # -------------------------------------------------------------------------------------------------------------
        # Exporting results
        # -------------------------------------------------------------------------------------------------------------
        export_tabular_data(
            config,
            self.output_basepath,
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

        config.to_config_file(Path(str(self.output_basepath) + "_config.ini"))

        # -------------------------------------------------------------------------------------------------------------
        print("---------------------------------------------")
        print("End of process!")
        print("---------------------------------------------")
        print("Total time:", "   %.2f" % elapsed_t, "s")
        print("nº of trees:", X_c.shape[0])
