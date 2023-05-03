import configparser
from pathlib import Path

from three_d_fin.processing.configuration import FinConfiguration


def test_load_from_file():
    """Test configuration consistency.

    Load a valid config file with a non-default parameter (lower_limit).
    Parse it as an object and check that the lower_limit field is not set to
    default value anymore.

    Additionally do an obvious check: a parsed config file is equivalent to the
    same file loaded via static method From_config_file().
    """
    config_file = configparser.ConfigParser()
    config_file.read(Path("tests/lowerlimitchange.ini").resolve())
    valid_config = FinConfiguration.parse_obj(config_file)

    assert valid_config.basic.lower_limit == config_file.getfloat(
        "basic", "lower_limit"
    )

    assert valid_config == FinConfiguration.From_config_file(
        Path("tests/lowerlimitchange.ini")
    )


def test_write_to_file():
    """Test configuration file writing."""
    config = FinConfiguration()
    config.to_config_file(Path("tests/configtest.ini"))
