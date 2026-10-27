"""Runs stages in order, with resume support and dependency checks."""
from __future__ import annotations

from .casa_api import CasaAPI
from .config import Config, load_config
from .context import PipelineContext
from .stages import ALL_STAGES


class Pipeline:
    def __init__(self, config: Config, casa: CasaAPI | None = None):
        self.stages = [cls() for cls in ALL_STAGES]
        self.ctx = PipelineContext(config=config, casa=casa or CasaAPI())
        self.ctx.load()  # pick up tables and progress from an earlier run

    @classmethod
    def from_yaml(cls, path, **kw) -> "Pipeline":
        return cls(load_config(path), **kw)

    @property
    def stage_names(self) -> list[str]:
        return [s.name for s in self.stages]

    def run(self, stages: list[str] | None = None) -> None:
        """Run the named stages (default: all), in pipeline order."""
        unknown = set(stages or []) - set(self.stage_names)
        if unknown:
            raise ValueError(f"Unknown stages {sorted(unknown)}; "
                             f"choose from {self.stage_names}")
        ctx = self.ctx
        for stage in self.stages:
            if stages is not None and stage.name not in stages:
                continue
            missing = [r for r in stage.requires if r not in ctx.completed]
            if missing:
                raise RuntimeError(f"Stage '{stage.name}' requires {missing} "
                                   "to have been run first.")
            gone = ctx.registry.missing()
            if gone:
                raise RuntimeError(f"Calibration tables missing on disk: {gone}")
            ctx.casa.log(f"Stage {stage.order}: {stage.name}")
            ctx.registry.drop_stage(stage.name)
            stage.run(ctx)
            if stage.name not in ctx.completed:
                ctx.completed.append(stage.name)
            ctx.save()

    def export_script(self, path: str) -> None:
        self.ctx.casa.export_script(path)
