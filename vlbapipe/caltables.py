"""Registry of calibration tables, kept in apply order and persisted to disk.

This replaces the notebook's module-level ``gaintables`` / ``gc_tab_interp``
lists. Because the registry is saved after every stage, a later run can start
from any stage and still apply every table derived earlier.
"""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CalTable:
    path: str
    interp: str
    stage: str      # name of the stage that produced it
    order: int      # stage position in the pipeline; fixes apply order
    kind: str = ""  # e.g. 'tsys', 'gc', so later steps can exclude some


class CalRegistry:
    def __init__(self, tables: list[CalTable] | None = None):
        self._tables: list[CalTable] = list(tables or [])

    def add(self, table: CalTable) -> None:
        self._tables = [t for t in self._tables if t.path != table.path]
        self._tables.append(table)

    def drop_stage(self, stage: str) -> None:
        """Forget tables from a stage that is about to be re-run."""
        self._tables = [t for t in self._tables if t.stage != stage]

    def tables(self, before_order: int | None = None,
               exclude_kinds: tuple[str, ...] = ()) -> list[CalTable]:
        keep = [t for t in self._tables
                if (before_order is None or t.order < before_order)
                and t.kind not in exclude_kinds]
        return sorted(keep, key=lambda t: t.order)  # stable: ties keep insertion order

    def gaintables(self, **kw) -> list[str]:
        return [t.path for t in self.tables(**kw)]

    def interp(self, **kw) -> list[str]:
        return [t.interp for t in self.tables(**kw)]

    def missing(self) -> list[str]:
        return [t.path for t in self._tables if not os.path.exists(t.path)]

    def to_list(self) -> list[dict]:
        return [asdict(t) for t in self._tables]

    @classmethod
    def from_list(cls, rows: list[dict]) -> "CalRegistry":
        return cls([CalTable(**r) for r in rows])
