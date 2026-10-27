import dataclasses

import pytest

from vlbapipe.cli import main
from vlbapipe.config import ConfigError
from vlbapipe.scriptgen import generate_script


def test_parameters_substituted(config):
    config = dataclasses.replace(config, calibrate_phase="J1154+6022",
                                 sbd_timerange="09:17:00~09:18:00")
    text = generate_script(config)
    compile(text, "script", "exec")
    assert "refant = 'FD'" in text
    assert "CALIBRATE_PHASE = 'J1154+6022'" in text
    assert "sbd_timerange = '09:17:00~09:18:00'" in text
    assert "<FILL IN>.ms" not in text  # template defaults replaced


def test_auto_refant_rejected(config):
    with pytest.raises(ConfigError, match="refant"):
        generate_script(dataclasses.replace(config, refant="auto"))


def test_cli_refant_override(tmp_path):
    cfg = tmp_path / "c.json"
    cfg.write_text('{"vis": "t.ms", "fitsidi_files": ["t.idifits"], "refant": "auto",'
                   ' "calibrate_delay": "3C84", "calibrate_phase": "P", "observe_target": "T"}')
    out = tmp_path / "s.py"
    main(["generate", str(cfg), "-o", str(out), "--refant", "PT"])
    assert "refant = 'PT'" in out.read_text()


def test_quicklook_options(config):
    text = generate_script(dataclasses.replace(config, calibrate_phase="P",
                                               quicklook_calibrators=True,
                                               image_cell="0.2mas", image_imsize=640))
    assert "quicklook_calibrators = True" in text
    assert "image_cell = '0.2mas'" in text
    assert "image_imsize = 640" in text


def test_imaging_defaults_auto(config):
    text = generate_script(dataclasses.replace(config, calibrate_phase="P"))
    assert "image_cell = 'auto'" in text
    assert "image_imsize = 'auto'" in text
    assert "quicklook_calibrators = False" in text
