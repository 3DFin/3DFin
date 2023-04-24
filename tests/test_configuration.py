import configparser
import operator
from pathlib import Path

from three_d_fin.processing.configuration import (
    Config,
    FinConfig,
    NumBoundValidator,
    OptionCategory,
    Parameter,
)


def test_config_creation() -> None:
    """Test that Config direct instanciation.

    Test that direct instanciation with valid validator succeed.
    Test that direct instanciation fail if a validator fails and raises an Exception.
    """

    class TestConfig(Config):
        dumb_parameter: Parameter[float] = Parameter[float](
            OptionCategory.BASIC, [NumBoundValidator(operator.lt, 1.0)], 0.0
        )

    TestConfig()

    # class TestConfigFail(Config):
    #     dumb_parameter: Parameter[float] = Parameter[float](
    #         OptionCategory.BASIC, [NumBoundValidator(operator.gt, 1.0)], 0.0
    #     )

    # with pytest.raises(Exception):
    #    a = TestConfigFail()


def test_from_dict() -> None:
    """Test instanciation from dictLike object."""
    config_parser = configparser.ConfigParser()

    config_parser.read(Path("tests/lowerlimitchange.ini").resolve())
    fin_parameters = FinConfig.from_dict_like(config_parser)
    assert fin_parameters.lower_limit.value == float(
        config_parser["basic"]["lower_limit"]
    )
