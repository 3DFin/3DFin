import configparser
import operator
from pathlib import Path

import pytest
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

    with pytest.raises(Exception):

        class TestConfigFail(Config):
            dumb_parameter: Parameter[float] = Parameter[float](
                OptionCategory.BASIC, [NumBoundValidator(operator.gt, 1.0)], 0.0
            )

        TestConfigFail()


def test_3dFin_consistency() -> None:
    """Test configuration consistency.

    Test consistency between the 3DFin file embedded in the package folder and
    the FinConfig class definition
    """
    config_parser = configparser.ConfigParser()

    config_parser.read(Path("src/three_d_fin/3DFINconfig.ini").resolve())
    fin_file_config = FinConfig.from_dict_like(config_parser)
    assert fin_file_config.check_validity() is True

    fin_default_config = FinConfig()
    assert fin_default_config.check_validity() is True

    for param_file, param_default in zip(
        fin_file_config.get_params(), fin_default_config.get_params(), strict=True
    ):
        assert param_file[1].value() == param_default[1].value()

    fin_default_config.axis_downstep.from_value(-1.0)
    assert fin_default_config.check_validity() is False
    
    # restore
    fin_default_config.axis_downstep.from_value(fin_file_config.axis_downstep.value())
    assert fin_default_config.check_validity() is True

    # test dependency
    fin_default_config.maximum_height(fin_default_config.minimum_height() - 0.1)
    assert fin_default_config.check_validity() is False



def test_from_dict() -> None:
    """Test instanciation from dictLike object.

    Check a config is modified by the loaded config
    """
    config_parser = configparser.ConfigParser()

    config_parser.read(Path("tests/lowerlimitchange.ini").resolve())
    fin_parameters = FinConfig.from_dict_like(config_parser)

    assert fin_parameters.lower_limit.value() == float(
        config_parser["basic"]["lower_limit"]
    )
