"""Stage interface: one stage per pipeline stage, state lives in the context."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..caltables import CalTable
from ..context import PipelineContext


class Stage(ABC):
    name: str = ""
    order: int = 0
    requires: tuple[str, ...] = ()

    @abstractmethod
    def run(self, ctx: PipelineContext) -> None:
        ...

    def add_table(self, ctx: PipelineContext, path: str, interp: str,
                  kind: str = "") -> None:
        ctx.registry.add(CalTable(path=path, interp=interp, stage=self.name,
                                  order=self.order, kind=kind))

    def kwargs(self, ctx: PipelineContext, **defaults) -> dict:
        """Task arguments: stage defaults overridden by the user's config."""
        defaults.update(ctx.config.stage_overrides(self.name))
        return defaults
