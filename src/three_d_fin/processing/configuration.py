import configparser
from pathlib import Path
from typing import Optional

import laspy
from pydantic import (
    BaseModel,
    DirectoryPath,
    Field,
    FilePath,
    validator,
)


class BasicParameters(BaseModel):
    """Handle the "basic" parameters section."""

    # Name of the Z0 field in the LAS file containing the cloud.
    z0_name: str = Field(title="Normalized height field name", default="Z0")
    # Upper limit (vertical) of the stripe where it should be reasonable to find trunks with minimum presence of shrubs or branchs.
    upper_limit: float = Field(title="Stripe upper Limit", gt=0, default=3.5)
    # Lower limit (vertical) of the stripe where it should be reasonable to find trunks with minimum presence of shrubs or branchs.
    lower_limit: float = Field(title="Stripe lower Limit", gt=0, default=0.7)
    # Number of iterations of 'peeling off branches'.
    number_of_iterations: int = Field(title="Prunning intensity", ge=0, le=5, default=2)

    @validator("lower_limit")
    def less_than_higher(cls, v, values):
        """Validate lower_limit field againt upper_limit value."""
        if "upper_limit" in values and v >= values["upper_limit"]:
            raise ValueError(
                f"""Stripe lower limit ({v}) should be lower than Stripe upper Limit ({values["upper_limit"]})"""
            )  # TODO: names are hardcoded for now
        return v


class AdvancedParameters(BaseModel):
    """Handle the "advanced" parameters section."""

    # Maximum diameter expected for any section during circle fitting.
    maximum_diameter: float = Field(
        title="Expected maximum diameter", gt=0, default=1.0
    )
    # Points within this distance from tree axes will be considered as potential stem points.
    stem_search_diameter: float = Field(title="Stem search diameter", gt=0, default=2.0)
    # Lowest height
    minimum_height: float = Field(title="Lowest section", gt=0, default=0.3)
    # highest height
    maximum_height: float = Field(title="Highest section", gt=0, default=25.0)
    # sections are this long (z length)
    section_len: float = Field(title="Distance between sections", gt=0, default=0.2)
    # sections are this wide
    section_wid: float = Field(title="Section width", gt=0, default=0.05)

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
    # (x, y) voxel resolution during stem identification within the stripe
    res_xy_stripe: float = Field(title="(x, y) voxel resolution", gt=0, default=0.02)
    # (z) voxel resolution during stem identification within the stripe
    res_z_stripe: float = Field(title="(z) voxel resolution", gt=0, default=0.02)
    # minimum number of points per stem within the stripe (DBSCAN clustering).
    number_of_points: int = Field(title="Number of points", gt=0, default=1000)
    # Vicinity radius for PCA during stem identification within the stripe
    verticality_scale_stripe: float = Field(
        title="Vicinity radius (verticality computation)", gt=0, default=0.1
    )
    # Verticality threshold durig stem identification within the stripe
    verticality_thresh_stripe: float = Field(
        title="Verticality threshold", gt=0.0, lt=1.0, default=0.7
    )
    # only stems where points extend vertically throughout this range are considered.
    height_range: float = Field(title="Vertical Range", gt=0, default=0.7)

    ### Stem extraction and tree individualization ###
    # (x, y) voxel resolution during stem extraction and tree individualization
    res_xy: float = Field(title="(x, y) voxel resolution", gt=0, default=0.035)
    # (z) voxel resolution during stem extraction and tree individualization
    res_z: float = Field(title="(z) voxel resolution", gt=0, default=0.035)
    # Minimum number of points within a stripe to consider it as a potential tree during
    # stem extraction and tree individualization
    minimum_points: int = Field(title="Minimum points", gt=0, default=20)
    # Vicinity radius for PCA  during stem extraction and tree individualization
    verticality_scale_stems: float = Field(
        title="Vicinity radius (verticality computation)", gt=0, default=0.1
    )
    # Verticality threshold  during stem extraction and tree individualization
    verticality_thresh_stems: float = Field(
        title="Verticality threshold", gt=0, lt=1, default=0.7
    )
    # Points that are closer than d_max to an axis are assigned to that axis during 
    # stem extraction and tree individualization.
    maximum_d: float = Field(title="Maximum distance to tree axis", gt=0, default=15.0)
    # Points within this distance from tree axes will be used to find tree height
    distance_to_axis: float = Field(title="Distance from axis", gt=0, default=1.5)
    # Resolution for the voxelization while computing tree heights
    res_heights: float = Field(
        title="Voxel resolution for height computation", gt=0, default=0.3
    )
    # Maximum degree of vertical deviation from the axis
    maximum_dev: float = Field(
        title="Maximum vertical deviation from axis", gt=0, default=25.0
    )

    ### Extracting sections ###
    # Minimum number of points in a section to be considered
    number_points_section: int = Field(title="Points within section", gt=0, default=80)
    # Proportion, regarding the circumference fit by fit_circle, that the inner circumference radius will have as length
    diameter_proportion: float = Field(
        title="Inner/outer circle proportion", ge=0.0, le=1.0, default=0.5
    )
    # Minimum diameter expected for any section circle fitting.
    minimum_diameter: float = Field(
        title="Minimum expected diameter", gt=0, default=0.06
    )
    # Number of points inside the inner circle
    point_threshold: int = Field(title="Points within inner circle", gt=0, default=5)
    # Maximum distance among points to be considered within the same cluster.
    point_distance: float = Field(title="Maximum point distance", gt=0, default=0.02)
    # Number of sectors in which the circumference will be divided
    number_sectors: int = Field(title="Number of sectors", gt=0, default=16)
    # Minimum number of sectors that must be occupied.
    m_number_sectors: int = Field(title="Number of occupied sectors", gt=0, default=9)
    # Width, in meters, around the circumference to look for points
    circle_width: float = Field(title="Circle width", gt=0, default=0.02)

    ### Drawing circles and axes ###
    # Number of points used to draw the sections in the _circ LAS file
    circa: int = Field(title="N of points to draw each circle", gt=0, default=200)
    # Distance between points used to draw axes in the _axes LAS file
    p_interval: float = Field(
        title="Interval at which points are drawn", gt=0, default=0.01
    )
    # From the stripe centroid, how much (downwards direction) will the drawn axes extend.
    axis_downstep: float = Field(
        title="Axis downstep from stripe center", gt=0, default=0.5
    )
    # From the stripe centroid, how much (upwards direction) will the drawn axes extend.
    axis_upstep: float = Field(
        title="Axis upstep from stripe center", gt=0, default=10.0
    )

    ### Height-normalization ###
    # Voxel resolution for cloth simulation and denoising process
    res_ground: float = Field(title="(x, y) voxel resolution", gt=0, default=0.15)
    # During the cleanning process, DBSCAN clusters whith size smaller than this value
    # will be considered as noise
    min_points_ground: int = Field(title="Minimum number of points", gt=0, default=2)
    # Resolution of cloth grid
    res_cloth: float = Field(title="Cloth resolution", gt=0, default=0.7)


class MiscParameters(BaseModel):
    """Handle the "misc" parameters section."""

    is_normalized: bool = Field(title="Is cloud normalized", default=False)
    is_noisy: bool = Field(title="Is cloud noisy", default=False)
    export_txt: bool = Field(title="Export tabular data to txt", default=False)
    # input file is not mandatory and could be provided by another mean.
    input_file: Optional[FilePath] = Field(title="Input file", default=None)
    output_dir: DirectoryPath = Field(
        title="Output dir", default_factory=lambda: Path.home()
    )

    @validator("input_file")
    def valid_input_las(cls, v: Optional[FilePath]):
        """Validate maximum_height field again minimum_height value."""
        if v is None:
            return v
        try:
            laspy.open(v.resolve(), read_evlrs=False)
        except laspy.LaspyException:
            raise ValueError("invalid las file") from None
        return v


class FinConfiguration(BaseModel):
    """Handle the parameters for 3DFin Application."""

    basic: BasicParameters = BasicParameters()
    advanced: AdvancedParameters = AdvancedParameters()
    expert: ExpertParameters = ExpertParameters()
    misc: Optional[MiscParameters] = MiscParameters()  # Misc parameters are optional.

    @classmethod
    def From_config_file(
        cls: "FinConfiguration", filename: Path, init_misc: bool = False
    ) -> "FinConfiguration":
        """Import parameters from a .ini file. The misc parameter could be initialized if not present.

        Could raise exceptions (ValidationError, FileNotFound, configparser.Error)


        Parameters
        ----------
        filename: Path
            the Path to the .ini file to load
        init_misc: bool
            whenether to init "misc" section to default if not present in the file

        Returns
        -------
            A validated FinConfiguration
        """
        parser = configparser.ConfigParser()
        # Could raise an Exception that the caller is resposible to catch
        with filename.open("r") as f:
            parser = configparser.ConfigParser()
            parser.read_file(f)
            config = cls.parse_obj(parser)
            if init_misc is False and config.misc is None:
                return config
            return FinConfiguration(
                basic=config.basic,
                advanced=config.advanced,
                expert=config.expert,
                misc=MiscParameters(),
            )

    def to_config_file(self, filename: Path):
        """Import parameters from a .ini file.

        Could raise exceptions (ValidationError, FileNotFound, configparser.Error)


        Parameters
        ----------
        filename: Path
            the Path to the .ini file to save
        """
        parser = configparser.ConfigParser()
        # Could raise an Exception that the caller is resposible to catch
        with filename.open("w") as f:
            parser = configparser.ConfigParser()
            parameter_dict = self.dict()
            # We remove optional sections, it's not supported by the parser
            if parameter_dict["misc"] is None:
                parameter_dict.pop("misc")
            elif parameter_dict["misc"]["input_file"] is None:
                parameter_dict["misc"].pop("input_file")
            parser.read_dict(parameter_dict)
            parser.write(f)
