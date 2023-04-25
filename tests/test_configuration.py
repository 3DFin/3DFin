import configparser
from pathlib import Path

from three_d_fin.processing.configuration import FinConfiguration


def test_load_from_file():
    config_file = configparser.ConfigParser()
    config_file.read(Path("tests/lowerlimitchange.ini").resolve())
    valid_config = FinConfiguration.parse_obj(config_file)
    assert valid_config.basic.lower_limit == config_file.getfloat(
        "basic", "lower_limit"
    )
    assert valid_config == FinConfiguration.From_config_file(
        Path("tests/lowerlimitchange.ini")
    )
