import pytest

from vlbapipe.config import Config, ConfigError


def test_placeholder_rejected():
    with pytest.raises(ConfigError, match="FILL IN"):
        Config(vis="a.ms", fitsidi_files=["<FILL IN>.IDI1"],
               calibrate_delay="x", observe_target="y")


def test_bandpass_defaults_to_delay(config):
    assert config.calibrate_bandpass == "3C84"


def test_missing_required():
    with pytest.raises(ConfigError, match="calibrate_delay"):
        Config(vis="a.ms", fitsidi_files=["a"], observe_target="y")


def test_bad_imsize_rejected():
    with pytest.raises(ConfigError, match="image_imsize"):
        Config(vis="a.ms", fitsidi_files=["a"], calibrate_delay="x",
               observe_target="y", image_imsize="big")
