"""Pipeline state shared between stages, persisted so runs can resume."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from .caltables import CalRegistry
from .casa_api import CasaAPI
from .config import Config

STATE_FILE = "vlbapipe_state.json"


@dataclass
class PipelineContext:
    config: Config
    casa: CasaAPI
    registry: CalRegistry = field(default_factory=CalRegistry)
    completed: list[str] = field(default_factory=list)
    refant: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def vis(self) -> str:
        return self.config.path(self.config.vis)

    @property
    def vis_pre(self) -> str:
        return self.config.path(self.config.vis_pre)

    @property
    def cal_vis(self) -> str:
        return self.config.path(self.config.cal_vis)

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        self.casa.log("WARNING: " + message, "WARN")

    @property
    def state_path(self) -> str:
        return self.config.path(STATE_FILE)

    def save(self) -> None:
        state = {"completed": self.completed, "refant": self.refant,
                 "tables": self.registry.to_list()}
        os.makedirs(self.config.workdir, exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=2)

    def load(self) -> bool:
        if not os.path.exists(self.state_path):
            return False
        with open(self.state_path) as f:
            state = json.load(f)
        self.completed = state["completed"]
        self.refant = state["refant"]
        self.registry = CalRegistry.from_list(state["tables"])
        return True
