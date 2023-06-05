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
    z0_name: str = Field(
        title="Normalized height field name",
        description="Name of the Z0 field in the point cloud. \n"
        "If the normalized heights are stored in the Z coordinate "
        'of the point cloud, then: Z0 field name = "z" (lowercase). ',
        default="Z0",
    )
    # Upper limit (vertical) of the stripe where it should be reasonable to find trunks with minimum presence of shrubs or branchs.
    upper_limit: float = Field(
        title="Stripe upper Limit",
        description="Upper (vertical) limit of the stripe where it should be reasonable "
        "to find stems with minimum presence of shrubs or branches. \n"
        "Reasonable values are 2-5 meters.",
        gt=0,
        default=3.5,
        hint="meters",
    )
    # Lower limit (vertical) of the stripe where it should be reasonable to find trunks with minimum presence of shrubs or branchs.
    lower_limit: float = Field(
        title="Stripe lower Limit",
        description="Lower (vertical) limit of the stripe where it should be reasonable "
        "to find stems with minimum presence of shrubs or branches. \n"
        "Reasonable values are 0.3-1.3 meters.",
        gt=0,
        default=0.7,
        hint="meters",
    )
    # Number of iterations of 'peeling off branches'.
    number_of_iterations: int = Field(
        title="Prunning intensity",
        description='Number of iterations of "pruning" during stem identification. \n'
        "Values between 1 (slight stem peeling/cleaning) "
        "and 5 (extreme branch peeling/cleaning).",
        ge=0,
        le=5,
        default=2,
        hint="0-5",
    )

    @validator("lower_limit")
    def less_than_higher(cls, v, values):
        """Validate lower_limit field againt upper_limit value."""
        if "upper_limit" in values and v >= values["upper_limit"]:
            raise ValueError(
                f"""Stripe lower limit ({v}) should be lower than Stripe upper Limit ({values["upper_limit"]})"""
            )
        return v


class AdvancedParameters(BaseModel):
    """Handle the "advanced" parameters section."""

    # Maximum diameter expected for any section during circle fitting.
    maximum_diameter: float = Field(
        title="Expected maximum diameter",
        description="Maximum diameter expected for any stem.",
        gt=0,
        default=1.0,
        hint="meters",
    )
    # Points within this distance from tree axes will be considered as potential stem points.
    stem_search_diameter: float = Field(
        title="Stem search diameter",
        description="Points within this distance from tree axes will be considered "
        "as potential stem points.\n"
        "Reasonable values are 'Maximum diameter'<2 meters "
        "(exceptionally greater than 2: very large diameters and/or intricate stems).",
        gt=0,
        default=2.0,
        hint="meters",
    )
    # Lowest height
    minimum_height: float = Field(
        title="Lowest section",
        description="Lowest height at which stem diameter will be computed.",
        gt=0,
        default=0.3,
        hint="meters",
    )
    # highest height
    maximum_height: float = Field(
        title="Highest section",
        description="Highest height at which stem diameter will be computed.",
        gt=0,
        default=25.0,
        hint="meters",
    )
    # sections are this long (z length)
    section_len: float = Field(
        title="Distance between sections",
        description="Height of the sections (z length). Diameters will then be "
        "computed for every section.",
        gt=0,
        default=0.2,
        hint="meters",
    )
    # sections are this wide
    section_wid: float = Field(
        title="Section width",
        description="Sections are this wide. This means that points within this distance "
        "(vertical) are considered during circle fitting and diameter coumputation.",
        gt=0,
        default=0.05,
        hint="meters",
    )

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
    res_xy_stripe: float = Field(
        title="(x, y) voxel resolution",
        description="(x, y) voxel resolution during stem extraction.",
        gt=0,
        default=0.02,
        hint="meters",
    )
    # (z) voxel resolution during stem identification within the stripe
    res_z_stripe: float = Field(
        title="(z) voxel resolution",
        description="(z) voxel resolution during stem extraction.",
        gt=0,
        default=0.02,
        hint="meters",
    )
    # minimum number of points per stem within the stripe (DBSCAN clustering).
    number_of_points: int = Field(
        title="Number of points",
        description="minimum number of points (voxels) per stem within the stripe "
        "(DBSCAN clustering). Reasonable values are between 500 and 3000.",
        gt=0,
        default=1000,
    )
    # Vicinity radius for PCA during stem identification within the stripe
    verticality_scale_stripe: float = Field(
        title="Vicinity radius (verticality computation)",
        description="Vicinity radius for PCA during stem identification.",
        gt=0,
        default=0.1,
        hint="meters",
    )
    # Verticality threshold durig stem identification within the stripe
    verticality_thresh_stripe: float = Field(
        title="Verticality threshold",
        description="Verticality threshold durig stem identification.\n"
        "Verticality is defined as (1 - sin(V)), being V the vertical angle of the "
        "normal vector, measured from the horizontal. "
        "Note that it does not grow linearly.",
        gt=0.0,
        lt=1.0,
        default=0.7,
        hint="(0, 1)",
    )
    # Only stems where points extend vertically throughout this range are considered.
    height_range: float = Field(
        title="Vertical Range",
        description="Proportion (0: none - 1: all) of the vertical range of the stripe "
        "that points need to extend through to be valid stems.",
        ge=0,
        le=1,
        default=0.7,
        hint="[0, 1]",
    )

    ### Stem extraction and tree individualization ###
    # (x, y) voxel resolution during stem extraction and tree individualization
    res_xy: float = Field(
        title="(x, y) voxel resolution",
        description="(x, y) voxel resolution during tree individualization.",
        gt=0,
        default=0.035,
        hint="meters",
    )
    # (z) voxel resolution during stem extraction and tree individualization
    res_z: float = Field(
        title="(z) voxel resolution",
        description="(z) voxel resolution during tree individualization.",
        gt=0,
        default=0.035,
        hint="meters",
    )
    # Minimum number of points within a stripe to consider it as a potential tree during
    # stem extraction and tree individualization
    minimum_points: int = Field(
        title="Minimum points",
        description="Minimum number of points (voxels) within a stripe to consider it "
        "as a potential tree during tree individualization.",
        gt=0,
        default=20,
    )
    # Vicinity radius for PCA  during stem extraction and tree individualization
    verticality_scale_stems: float = Field(
        title="Vicinity radius (verticality computation)",
        description="Vicinity radius for PCA during tree individualization.",
        gt=0,
        lt=1.0,
        default=0.1,
        hint="meters",
    )
    # Verticality threshold  during stem extraction and tree individualization
    verticality_thresh_stems: float = Field(
        title="Verticality threshold",
        description="Verticality threshold durig stem extraction.\n"
        "Verticality is defined as (1 - sin(V)), being V the vertical angle of the "
        "normal vector, measured from the horizontal.\n"
        "Note that it does not grow linearly.",
        default=0.7,
        gt=0.0,
        le=1.0,
        hint="(0, 1)",
    )
    # Points that are closer than d_max to an axis are assigned to that axis during
    # stem extraction and tree individualization.
    maximum_d: float = Field(
        title="Maximum distance to tree axis",
        description="Points that are closer than this distance to an axis "
        "are assigned to that axis during tree individualization process.",
        gt=0.0,
        default=15.0,
        hint="meters",
    )
    # Points within this distance from tree axes will be used to find tree height
    distance_to_axis: float = Field(
        title="Distance from axis",
        description="Maximum distance from tree axis at which points will "
        "be considered while computing tree height.\n"
        "Points too far away from the tree axis might not be representative"
        "of actual tree height.",
        gt=0,
        default=1.5,
        hint="meters",
    )
    # Resolution for the voxelization while computing tree heights
    res_heights: float = Field(
        title="Voxel resolution for height computation",
        description="(x, y, z) voxel resolution during tree height computation.",
        gt=0,
        default=0.3,
        hint="meters",
    )
    # Maximum degree of vertical deviation from the axis
    maximum_dev: float = Field(
        title="Maximum vertical deviation from axis",
        description="Maximum degree of vertical deviation from the axis for "
        "a tree height to be considered as valid.",
        gt=0,
        default=25.0,
        hint="degrees",
    )

    ### Extracting sections ###
    # Minimum number of points in a section to be considered as valid
    number_points_section: int = Field(
        title="Points within section",
        description="Minimum number of points in a section to be considered as valid.",
        gt=0,
        default=80,
    )
    # Proportion, regarding the circumference fit by fit_circle, that the inner circumference radius will have as length
    diameter_proportion: float = Field(
        title="Inner/outer circle proportion",
        description="Proportion, regarding the circumference fit by fit_circle, "
        "that the inner circumference diameter will have as length.",
        ge=0.0,
        le=1.0,
        default=0.5,
        hint="[0, 1]",
    )
    # Minimum diameter expected for any section circle fitting.
    minimum_diameter: float = Field(
        title="Minimum expected diameter",
        description="Minimum diameter expected for any section during circle fitting.",
        gt=0,
        default=0.06,
        hint="meters",
    )
    # Number of points inside the inner circle
    point_threshold: int = Field(
        title="Points within inner circle",
        description="Maximum number of points inside the inner circle"
        "to consider the fitting as OK.",
        gt=0,
        default=5,
    )
    # Maximum distance among points to be considered within the same cluster.
    point_distance: float = Field(
        title="Maximum point distance",
        description="Maximum distance among points to be considered within the "
        "same cluster during circle fitting.",
        gt=0,
        default=0.02,
        hint="meters",
    )
    # Number of sectors in which the circumference will be divided
    number_sectors: int = Field(
        title="Number of sectors",
        description="Number of sectors in which the circumference will be divided",
        gt=0,
        default=16,
    )
    # Minimum number of sectors that must be occupied.
    m_number_sectors: int = Field(
        title="Number of occupied sectors",
        description="Minimum number of sectors that must be occupied.",
        gt=0,
        default=9,
    )
    # Width, in meters, around the circumference to look for points
    circle_width: float = Field(
        title="Circle width",
        description="Width, in meters, around the circumference to look" "for points.",
        gt=0,
        default=0.02,
        hint="meters",
    )

    ### Drawing circles and axes ###
    # Number of points used to draw the sections in the _circ file/cloud
    circa: int = Field(
        title="N of points to draw each circle",
        description="Number of points that will be used to draw the circles",
        gt=0,
        default=200,
    )
    # Distance between points used to draw axes in the _axes file/cloud
    p_interval: float = Field(
        title="Interval at which points are drawn while drawing",
        description="Distance at which points will be placed from one to another"
        "while drawing the axes point cloud",
        gt=0,
        default=0.01,
        hint="meters",
    )
    # From the stripe centroid, how much (downwards direction) will the drawn axes extend.
    axis_downstep: float = Field(
        title="Axis downstep from stripe center",
        description="From the stripe centroid, how much (downwards direction) "
        "will the drawn axes extend.\nBasically, this parameter controls"
        "from where will the axes be drawn.",
        gt=0,
        default=0.5,
        hint="meters",
    )
    # From the stripe centroid, how much (upwards direction) will the drawn axes extend.
    axis_upstep: float = Field(
        title="Axis upstep from stripe center",
        description="From the stripe centroid, how much (upwards direction) "
        "will the drawn axes extend.\nBasically, this parameter control"
        "how long will the drawn axes be.",
        gt=0,
        default=10.0,
        hint="meters",
    )

    ### Height-normalization ###
    # Voxel resolution for cloth simulation and denoising process
    res_ground: float = Field(
        title="(x, y) voxel resolution",
        description="(x, y, z) voxel resolution during denoising.\n"
        "Note that the whole point cloud is voxelated.",
        gt=0,
        default=0.15,
        hint="meters",
    )
    # During the cleanning process, DBSCAN clusters whith size smaller than this value
    # will be considered as noise
    min_points_ground: int = Field(
        title="Minimum number of points",
        description="Clusters with size smaller than this value will be"
        "regarded as noise and thus eliminated.",
        gt=0,
        default=2,
    )
    # Resolution of cloth grid
    res_cloth: float = Field(
        title="Cloth resolution",
        description="Initial cloth grid resolution to generate the DTM that"
        "be used to compute normalized heights.",
        gt=0,
        default=0.7,
        hint="meters",
    )


class MiscParameters(BaseModel):
    """Handle the "misc" parameters section."""

    is_normalized: bool = Field(
        title="Normalize point cloud",
        description="If the point cloud is not height-normalized, a Digital Terrain "
        "Model will be generated to compute normalized heights for all points.",
        default=False,
    )  # TODO change = do_normalize, default True
    is_noisy: bool = Field(
        title="Clean noise on DTM",
        description="If it is expected to be noise below ground level (or if you know "
        "that there is noise), a denoising step will be added before "
        "generating the Digital Terrain Model.",
        default=False,
    )
    export_txt: bool = Field(
        title="Format of output tabular data",
        description="Outputs are gathered in a xlsx (Excel) file by default.\n"
        'Selecting "TXT files" will make the program output several txt files '
        "with the raw data, which may be more convenient for processing "
        "the data via scripting.",
        default=False,
    )
    # input file is not mandatory and could be provided by another mean.
    input_file: Optional[FilePath] = Field(
        title="Input file", description="Input File (*.las, *.laz)", default=None
    )
    output_dir: DirectoryPath = Field(
        title="Output dir",
        description="output directory",
        default_factory=lambda: Path.home(),
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
            whether to init "misc" section to default parameters if not present in the file

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

    @classmethod
    def field_tooltip(cls: "FinConfiguration", category_key: str, field_key: str):
        """Generate a tooltip text for a given field.

        Parameters
        ----------
        category_key: str
            the key (name) of the category of the field
        field_key: str
            the key (name) of the field
        """
        field = cls.__fields__.get(category_key).type_.__fields__.get(field_key)
        description = field.field_info.description
        default_txt = f"Default: {field.field_info.default}"
        if description is None:
            tooltip_txt = f"{default_txt}"
        else:
            tooltip_txt = f"{description}\n{default_txt}"
        return tooltip_txt

    @classmethod
    def field_hint(cls: "FinConfiguration", category_key: str, field_key: str):
        """Generate a hint text for a given field.

        Parameters
        ----------
        category_key: str
            the key (name) of the category of the field
        field_key: str
            the key (name) of the field
        """
        field = cls.__fields__.get(category_key).type_.__fields__.get(field_key)
        hint = field.field_info.extra.pop("hint", "")
        return str(hint)

    @classmethod
    def field_type(cls: "FinConfiguration", category_key: str, field_key: str):
        """Return type of a given field.

        Parameters
        ----------
        category_key: str
            the key (name) of the category of the field
        field_key: str
            the key (name) of the field
        """
        cls.__fields__.get(category_key).type_.__fields__.get(field_key)
        return cls.__fields__.get(category_key).type_.__fields__.get(field_key).type_

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
