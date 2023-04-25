import configparser
from pathlib import Path
from typing import Self

from pydantic import (
    BaseModel,
    DirectoryPath,
    FilePath,
    PositiveFloat,
    PositiveInt,
    confloat,
    conint,
    validator,
)


class BasicParameters(BaseModel):
    """Handle the "basic" parameters section."""

    # Name of the Z0 field in the LAS file containing the cloud.
    z0_name: str = "Z0"
    # Upper limit (vertical) of the stripe where it should be reasonable to find trunks with minimum presence of shrubs or branchs.
    upper_limit: PositiveFloat = 3.5
    # Lower limit (vertical) of the stripe where it should be reasonable to find trunks with minimum presence of shrubs or branchs.
    lower_limit: PositiveFloat = 0.7
    # Number of iterations of 'peeling off branches'.
    number_of_iterations: conint(ge=0, le=5) = 2

    @validator("lower_limit")
    def less_than_higher(cls, v, values):
        """Validate lower_limit field againt upper_limit value."""
        if "upper_limit" in values and v >= values["upper_limit"]:
            raise ValueError(
                f"""lower_limit ({v}) should be lower than upper_limit ({values["upper_limit"]})"""
            )
        return v


class AdvancedParameters(BaseModel):
    """Handle the "advanced" parameters section."""

    # Maximum diameter expected for any section during circle fitting.
    maximum_diameter: PositiveFloat = 1.0
    # Points within this distance from tree axes will be considered as potential stem points.
    stem_search_diameter: PositiveFloat = 2.0
    # Lowest height
    minimum_height: PositiveFloat = 0.3
    # highest height
    maximum_height: PositiveFloat = 25.0
    # sections are this long (z length)
    section_len: PositiveFloat = 0.2
    # sections are this wide
    section_wid: PositiveFloat = 0.05

    @validator("maximum_height")
    def more_than_mini(cls, v, values):
        """Validate maximum_height field again minimum_height value."""
        if "minimum_height" in values and v <= values["minimum_height"]:
            raise ValueError(
                f"""maximum_height ({v}) should be higher than minimum_height ({values["minimum_height"]})"""
            )
        return v


class ExpertParameters(BaseModel):
    """Handle the "expert" parameters section."""

    ### Stem identification whithin the stripe ###
    # (x, y) voxel resolution during stem extraction
    res_xy_stripe: PositiveFloat = 0.02
    # (z) voxel resolution during stem extraction
    res_z_stripe: PositiveFloat = 0.02
    # minimum number of points per stem within the stripe (DBSCAN clustering).
    number_of_points: PositiveInt = 1000
    # Vicinity radius for PCA during stem extraction
    verticality_scale_stripe: confloat(gt=0.0, lt=1.0) = 0.1
    # Verticality threshold durig stem extraction
    verticality_thresh_stripe: PositiveFloat = 0.7
    ### Stem extraction and tree individualization ###
    # (x, y) voxel resolution during tree individualization
    res_xy: PositiveFloat = 0.035
    # (z) voxel resolution during tree individualization
    res_z: PositiveFloat = 0.035
    # Minimum number of points within a stripe to consider it as a potential tree during tree individualization
    minimum_points: PositiveInt = 20
    # Vicinity radius for PCA  during tree individualization
    verticality_scale_stems: PositiveFloat = 0.1
    # Verticality threshold  during tree individualization
    verticality_thresh_stems: confloat(gt=0, lt=1) = 0.7
    # only stems where points extend vertically throughout this range are considered.
    height_range: PositiveFloat = 0.7
    # Points that are closer than d_max to an axis are assigned to that axis during individualize_trees process.
    maximum_d: PositiveFloat = 15.0
    # Points within this distance from tree axes will be used to find tree height
    distance_to_axis: PositiveFloat = 1.5
    # Resolution for the voxelization while computing tree heights
    res_heights: PositiveFloat = 0.3
    # Maximum degree of vertical deviation from the axis
    maximum_dev: PositiveFloat = 25.0
    ### Extracting sections ###
    # Minimum number of points in a section to be considered
    number_points_section: PositiveInt = 80
    # Proportion, regarding the circumference fit by fit_circle, that the inner circumference radius will have as length
    diameter_proportion: confloat(ge=0.0, le=1.0) = 0.5
    # Minimum diameter expected for any section circle fitting.
    minimum_diameter: PositiveFloat = 0.06
    # Number of points inside the inner circle
    point_threshold: PositiveInt = 5
    # Maximum distance among points to be considered within the same cluster.
    point_distance: PositiveFloat = 0.02
    # Number of sectors in which the circumference will be divided
    number_sectors: PositiveInt = 16
    # Minimum number of sectors that must be occupied.
    m_number_sectors: PositiveInt = 9
    # Width, in meters, around the circumference to look for points
    circle_width: PositiveFloat = 0.02
    ### Drawing circles and axes ###
    # Number of points used to draw the sections in the _circ LAS file
    circa: PositiveInt = 200
    # Distance between points used to draw axes in the _axes LAS file
    p_interval: PositiveFloat = 0.01
    # From the stripe centroid, how much (downwards direction) will the drawn axes extend.
    axis_downstep: PositiveFloat = 0.5
    # From the stripe centroid, how much (upwards direction) will the drawn axes extend.
    axis_upstep: PositiveFloat = 10.0
    ### Height-normalization ###
    # Voxel resolution for cloth simulation and denoising process
    res_ground: PositiveFloat = 0.15
    # During the cleanning process, DBSCAN clusters whith size smaller than this value
    # will be considered as noise
    min_points_ground: PositiveInt = 2
    # Resolution of cloth grid
    res_cloth: PositiveFloat = 0.7


class MiscParameters(BaseModel):
    """Handle the "misc" parameters section."""

    is_normalized: bool = True
    is_noisy: bool = False
    export_txt: bool = False
    # input file is not mandatory and could be provided by another mean.
    input_file: FilePath | None = None
    output_dir: DirectoryPath = None


class FinConfiguration(BaseModel):
    """Handle the parameters for 3DFin Application."""

    basic: BasicParameters = BasicParameters()
    advanced: AdvancedParameters = AdvancedParameters()
    expert: ExpertParameters = ExpertParameters()
    misc: MiscParameters | None = None  # Misc parameters are optional.

    @classmethod
    def From_config_file(cls: Self, filename: Path) -> "FinConfiguration":
        """Import parameters from a .ini file.

        Could raise exceptions (ValidationError, FileNotFound, configparser.Error)


        Parameters
        ----------
        filename: Path
            the Path to the .ini file to load


        Returns
        -------
            A validated FinConfiguration
        """
        parser = configparser.ConfigParser()
        # could raise an Exception that the caller is resposible to catch
        with filename.open("r") as f:
            parser = configparser.ConfigParser()
            parser.read_file(f)
            return cls.parse_obj(parser)

    def to_config_file(self, filename: Path):
        """Import parameters from a .ini file.

        Could raise exceptions (ValidationError, FileNotFound, configparser.Error)


        Parameters
        ----------
        filename: Path
            the Path to the .ini file to save
        """
        parser = configparser.ConfigParser()
        # could raise an Exception that the caller is resposible to catch
        with filename.open("w") as f:
            parser = configparser.ConfigParser()
            parser.write(f, self.dict())
