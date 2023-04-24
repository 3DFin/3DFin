import inspect
import operator
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Generic, Mapping, Self, TypeVar, cast

T = TypeVar("T", str, float, int, bool)

N = TypeVar("N", float, int)


class Validator(ABC, Generic[T]):
    """Abstract interface for validators."""

    @abstractmethod
    def validate(self, value: T) -> None:
        """Validate a value.

        Return nothing but must raise a instance of ValidationError if
        it fails.

        Parameter
        ---------
        value : T
        """


class NumBoundValidator(Validator[N]):
    """Check for numeric bounds."""

    bound: N
    operator_callback: Callable[[N, N], bool]

    def __init__(self, operator_callback: Callable[[N, N], bool], bound: N) -> None:
        """Construct the validator.

        Parameters
        ----------
        bound : N
            Bound the value will be checked.
        operator_callback:  Callable[[N, N], bool
            Callback that will use int conjonction with value and bound to create the
            predicate.
        """
        self.bound = bound
        self.operator_callback = operator_callback

    def validate(self, value: N) -> None:
        """Validate a value.

        Validate against predicate.
        """
        if not self.operator_callback(value, self.bound):
            raise ValidationError("Invalid bound check")


class ValidationError(Exception):
    """Exception raise by a validator."""

    msg: str

    def __init__(self, msg: str) -> None:
        """Embed only a simple message."""
        super().__init__()
        self.msg = msg


class ParameterState(Enum):
    """Enum compiling authorized states for Parameter."""

    VALID = 0
    INVALID = 1
    NOT_VALIDATED = (
        2  # Not really used yet but could be usefull if we implement lazy evaluations
    )


class OptionCategory(Enum):
    """Enum compiling authorized values for Parameter category."""

    BASIC = "basic"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MISC = "misc"


class Parameter(Generic[T]):
    """Configuration Parameter.

    An option Parameter is defined by an encapsulated value of Type T
    that could be a string, an int, a float or a bool. A default value
    should always be provided at construction time by the caller.
    A list of Validator could also be provided in order to check that the
    value conform to business rules/logic.
    If the value have to change, the caller is responsible for using setters
    (from_string, from_value) in order to enforce consistancy of the value with
    internal state because the object keep tracks of the validation state and
    the list of putatives error messages from validation.
    It also belongs to a Category to be used in conjunction with configParser
    """

    value: T
    validators: list[Validator[T]] | None
    category: OptionCategory
    state: ParameterState = ParameterState.NOT_VALIDATED
    error_msgs: list[str] = []

    def __init__(
        self,
        category: OptionCategory,
        validators: list[Validator[T]] | None,
        default: T,
    ):
        """Construct a Parameter object.

        Parameters
        ----------
        category : OptionCategory
            Category of parameter (usefull for using it in dictLike objects).
        validators : list[Validator[T]] | None
            Putative list of validators for the Parameter
        default : T
            Mandatory default value.
        """
        self.validators = validators
        self.category = category
        self.from_value(default)
        # Check if default is set according to validators, else raise an exception
        if self.state == ParameterState.INVALID:
            raise Exception

    def from_string(self, str_value: str) -> None:
        """Assign a Parameter value from a string representation.

        The string representation is casted to a T object and then it
        is passed to the "regular" from_value setter.

        Parameter
        ---------
            str_value : str
        """
        try:
            if isinstance(self.value, float):
                temp_value = float(str_value)
            elif isinstance(self.value, int):
                temp_value = int(str_value)
            elif isinstance(self.value, bool):
                temp_value = bool(str_value)
            else:
                temp_value = str_value
        except ValueError:
            self.state = ParameterState.INVALID
            self.error_msgs.append(
                f"Impossible to convert {str_value}"
            )  # TODO improve error message
        else:
            self.from_value(cast(T, temp_value))  # type: ignore[redundant-cast]

    def from_value(self, value: T) -> None:
        """Change a Parameter value.

        Run all validators against the value and eventually assign it to the internal value if
        it succeeds. If it fails the Parmater is leaved in an invalid state and error_msg is
        filled according to validation errors.

        Parameter
        ---------
            value : T
        """
        self.error_msgs = []
        self.state = (
            ParameterState.NOT_VALIDATED
        )  # not very usefull, but semantically fair.
        if self.validators is None:
            self.state = ParameterState.VALID
        else:
            for validator in self.validators:
                try:
                    validator.validate(value)
                    self.state = ParameterState.VALID
                except ValidationError as e:
                    self.state = ParameterState.INVALID
                    self.error_msgs.append(e.msg)
        # We won't let value uninitialized, so we assign it anyway
        self.value = value


class Config:
    """Base configuration class.

    A valid Config object should inherit from this class.
    """

    @classmethod
    def from_dict_like(cls, dict_like: Mapping[str, Mapping[str, Any]]) -> Self:
        """Construct a Config object from a dictLike object.

        Parameter
        ---------
            dict_like : Mapping[str, Mapping[str, Any]]
                The dict like object constaining the configuration.
                The first key is the category of the parameter.
        """
        config = cls()
        param_members: list[tuple[str, Parameter[T]]] = inspect.getmembers(  # type: ignore[valid-type]
            config, lambda member: isinstance(member, Parameter)
        )
        for param_name, param in param_members:
            param.from_string(dict_like[param.category.value][param_name])
        return config

    def get_params(self) -> list[tuple[str, Parameter[T]]]:
        """Get all parameters defined in the class.

        It could have been defined in a dict or in a list of parameters. All
        representation has its pro and cons. This implementation with parameters
        included as direct members of the class seems to ofer the best match for our use
        case for now.
        """
        return inspect.getmembers(  # type: ignore[valid-type]
            self, lambda member: isinstance(member, Parameter)
        )

    def check_validity(self) -> bool:
        """Return the current config validity.

        Returns
        -------
            is_valid : bool
                A boolean reflecting the current validity of the configuration
        """
        is_valid: bool = True
        for param in self.get_params():
            is_valid &= param[1].state == ParameterState.VALID
        return is_valid


class FinConfig(Config):
    """A dedicated 3DFin configuration class."""

    # Name of the Z0 field in the LAS file containing the cloud.
    z0_name = Parameter[str](OptionCategory.BASIC, None, "Z0")

    # Upper and lower limits (vertical) of the stripe where it should be reasonable to find stems with minimum presence of shrubs or branches.
    # TODO: in fact it is not hard limits here so we maybe have to relax the bounds
    upper_limit = Parameter[float](
        OptionCategory.BASIC,
        [NumBoundValidator(operator.ge, 2.0), NumBoundValidator(operator.le, 5.0)],
        3.5,
    )
    lower_limit = Parameter[float](
        OptionCategory.BASIC,
        [NumBoundValidator(operator.ge, 0.3), NumBoundValidator(operator.le, 1.3)],
        0.7,
    )
    # Number of iterations of 'peeling off branches'.
    # Values between 0 (no branch peeling/cleaning) and 5 (very extreme branch peeling/cleaning)
    number_of_iterations = Parameter[int](
        OptionCategory.BASIC,
        [NumBoundValidator(operator.ge, 0), NumBoundValidator(operator.le, 5)],
        2,
    )

    # # -------------------------------------------------------------------------------------------------
    # # Advanced PARAMETERS. They should only be modified when no good results are obtained tweaking basic parameters.
    # # They require a deeper knowledge of how the algorithm and the implementation work
    # # -------------------------------------------------------------------------------------------------

    # Points within this distance from tree axes will be considered as potential stem points.
    # Values between maximum diameter and 1 (exceptionally greater than 1: very large diameters and/or intricate stems)

    # Maximum radius expected for any section during circle fitting.
    # TODO: dendromatics needs radius from this input
    maximum_diameter = Parameter[float](
        OptionCategory.ADVANCED, [NumBoundValidator(operator.gt, 0.0)], 2.0
    )

    # TODO: dendromatics needs radius from this input
    stem_search_diameter = Parameter[float](
        OptionCategory.ADVANCED, [NumBoundValidator(operator.gt, 0.0)], 1.0
    )

    # Lowest height
    minimum_height = Parameter[float](
        OptionCategory.ADVANCED, [NumBoundValidator(operator.gt, 0.0)], 0.3
    )

    # highest height
    maximum_height = Parameter[float](
        OptionCategory.ADVANCED,
        [
            NumBoundValidator(operator.gt, 0.0),
        ],
        25.0,
    )

    # sections are this long (z length)
    section_len = Parameter[float](
        OptionCategory.ADVANCED, [NumBoundValidator(operator.gt, 0.0)], 0.2
    )

    # sections are this wide
    section_wid = Parameter[float](
        OptionCategory.ADVANCED, [NumBoundValidator(operator.gt, 0.0)], 0.05
    )

    # # -------------------------------------------------------------------------------------------------
    # # EXPERT PARAMETERS. They should only be modified when no good results are obtained peaking basic parameters.
    # # They require a deeper knowledge of how the algorithm and the implementation work
    # # *Stored in the main script in this version.
    # # -------------------------------------------------------------------------------------------------

    ### Stem identification whithin the stripe
    # (x, y) voxel resolution during stem extraction
    res_xy_stripe = Parameter[float](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0.0)], 0.02
    )

    # (z) voxel resolution during stem extraction
    res_z_stripe = Parameter[float](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0.0)], 0.02
    )

    # minimum number of points per stem within the stripe (DBSCAN clustering).
    number_of_points = Parameter[int](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0)], 1000
    )

    # Vicinity radius for PCA during stem extraction
    verticality_scale_stripe = Parameter[float](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0.0)], 0.1
    )

    # Verticality threshold during stem extraction
    verticality_thresh_stripe = Parameter[float](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0.0)], 0.7
    )

    # only stems where points extend vertically throughout this range are considered.
    height_range = Parameter[float](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0.0)], 0.7
    )

    # Points that are closer than d_max to an axis are assigned to that axis during individualize_trees process.
    maximum_d = Parameter[float](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0.0)], 15
    )

    # Points within this distance from tree axes will be used to find tree height
    distance_to_axis = Parameter[float](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0.0)], 1.5
    )

    # Resolution for the voxelization while computing tree heights
    res_heights = Parameter[float](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0.0)], 0.3
    )

    # Maximum degree of vertical deviation from the axis
    maximum_dev = Parameter[float](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0.0)], 25.0
    )

    ### Extracting sections ###
    # Minimum number of points in a section to be considered
    number_points_section = Parameter[int](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0)], 80
    )
    # Proportion, regarding the circumference fit by fit_circle, that the inner circumference radius will have as length
    diameter_proportion = Parameter[float](
        OptionCategory.EXPERT,
        [NumBoundValidator(operator.gt, 0.0), NumBoundValidator(operator.le, 1.0)],
        0.5,
    )
    # Minimum diameter expected for any section circle fitting.
    minimum_diameter = Parameter[float](
        OptionCategory.EXPERT,
        [NumBoundValidator(operator.gt, 0.0), NumBoundValidator(operator.le, 1.0)],
        0.06,
    )

    # Number of points inside the inner circle
    point_threshold = Parameter[int](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0)], 5
    )

    # Maximum distance among points to be considered within the same cluster.
    point_distance = Parameter[float](
        OptionCategory.EXPERT,
        [NumBoundValidator(operator.gt, 0.0), NumBoundValidator(operator.le, 1.0)],
        0.02,
    )
    # Number of sectors in which the circumference will be divided
    number_sectors = Parameter[int](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0)], 16
    )
    # Minimum number of sectors that must be occupied.
    m_number_sectors = Parameter[int](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0)], 9
    )
    # Width, in meters, around the circumference to look for points
    circle_width = Parameter[float](
        OptionCategory.EXPERT,
        [NumBoundValidator(operator.gt, 0.0), NumBoundValidator(operator.le, 1.0)],
        0.02,
    )

    ### Drawing circles and axes ###
    # Number of points used to draw the sections in the _circ LAS file
    circa = Parameter[int](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0)], 200
    )
    # Distance between points used to draw axes in the _axes LAS file
    p_interval = Parameter[float](
        OptionCategory.EXPERT,
        [NumBoundValidator(operator.gt, 0.0)],
        0.01,
    )
    # From the stripe centroid, how much (downwards direction) will the drawn axes extend.
    axis_downstep = Parameter[float](
        OptionCategory.EXPERT,
        [NumBoundValidator(operator.gt, 0.0)],
        0.05,
    )
    # From the stripe centroid, how much (upwards direction) will the drawn axes extend.
    axis_upstep = Parameter[float](
        OptionCategory.EXPERT,
        [NumBoundValidator(operator.gt, 0.0)],
        10.0,
    )
    ### Height-normalization ###
    # Voxel resolution for cloth simulation and denoising process
    res_ground = Parameter[float](
        OptionCategory.EXPERT,
        [NumBoundValidator(operator.gt, 0.0)],
        0.15,
    )
    # During the cleanning process, DBSCAN clusters whith size smaller than this value
    # will be considered as noise
    min_points_ground = Parameter[int](
        OptionCategory.EXPERT, [NumBoundValidator(operator.gt, 0)], 2
    )
    # Resolution of cloth grid
    res_cloth = Parameter[float](
        OptionCategory.EXPERT,
        [NumBoundValidator(operator.gt, 0.0)],
        0.7,
    )
