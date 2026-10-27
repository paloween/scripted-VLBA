"""User configuration: loaded from YAML/JSON, validated before CASA starts."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Config:
    # Data
    vis: str
    fitsidi_files: list[str]
    antab_file: str | None = None
    obs_freq_ghz: float | None = None
    workdir: str = "."

    # Field roles. bandpass defaults to delay (typical fringe-finder use).
    calibrate_delay: str = ""
    calibrate_bandpass: str = ""
    calibrate_phase: str = ""
    observe_target: str = ""

    # Reference antenna: a name/list such as 'FD,PT', or 'auto'.
    refant: str = "auto"

    # A priori flagging (step 2)
    quack_interval_s: float = 4.0
    tfcrop: bool = True
    manual_flags: bool = False
    manual_flag_spw: str = ""

    # Instrumental delay (step 7); '' = whole track
    sbd_timerange: str = ""

    phase_ref_target: bool = True

    # Antenna-position corrections (step 5); usually small for the VLBA
    antpos: bool = False

    # Imaging (self-cal and quicklook, steps 16-17). 'auto' derives the cell
    # from the longest baseline and the size from a fixed number of beams.
    image_cell: str = "auto"
    image_imsize: int | str = "auto"
    quicklook_calibrators: bool = False   # step 17: also image the calibrators

    # Per-stage task-argument overrides: {"fringefit": {"solint": "60s"}}
    overrides: dict[str, dict] = field(default_factory=dict)

    def __post_init__(self):
        if not self.calibrate_bandpass:
            object.__setattr__(self, "calibrate_bandpass", self.calibrate_delay)
        problems = self.validate()
        if problems:
            raise ConfigError("Invalid config:\n  - " + "\n  - ".join(problems))

    def validate(self) -> list[str]:
        problems = []
        for f in fields(self):
            value = getattr(self, f.name)
            values = value if isinstance(value, list) else [value]
            if any(isinstance(v, str) and "<FILL IN" in v for v in values):
                problems.append(f"'{f.name}' still contains a <FILL IN> placeholder")
        if not self.vis:
            problems.append("'vis' is required")
        if not self.fitsidi_files:
            problems.append("'fitsidi_files' must list at least one file")
        if not self.calibrate_delay:
            problems.append("'calibrate_delay' (fringe-finder field) is required")
        if not self.observe_target:
            problems.append("'observe_target' is required")
        if self.image_imsize != "auto" and not (
                isinstance(self.image_imsize, int) and self.image_imsize > 0):
            problems.append("'image_imsize' must be 'auto' or a positive integer")
        if self.obs_freq_ghz is not None and self.obs_freq_ghz <= 0:
            problems.append("'obs_freq_ghz' must be positive")
        return problems

    @property
    def vis_pre(self) -> str:
        return self.vis[:-3] if self.vis.endswith(".ms") else self.vis

    @property
    def cal_vis(self) -> str:
        return self.vis_pre + "_cal.ms"

    def path(self, name: str) -> str:
        return str(Path(self.workdir) / name)

    def stage_overrides(self, stage: str) -> dict:
        return dict(self.overrides.get(stage, {}))


def load_config(path: str | Path) -> Config:
    path = Path(path)
    text = path.read_text()
    if path.suffix == ".json":
        raw = json.loads(text)
    else:
        import yaml  # imported lazily so JSON configs and tests need no PyYAML

        raw = yaml.safe_load(text)
    known = {f.name for f in fields(Config)}
    unknown = set(raw) - known
    if unknown:
        raise ConfigError(f"Unknown config keys: {sorted(unknown)}")
    return Config(**raw)
