"""Notebook steps 0-1: import FITS-IDI, listobs, choose the reference antenna."""
from __future__ import annotations

import os

from ..heuristics.refant import rank_refants
from .base import Stage


class ImportData(Stage):
    name = "importdata"
    order = 0

    def run(self, ctx):
        cfg, casa = ctx.config, ctx.casa

        if not os.path.exists(ctx.vis):
            casa.importfitsidi(**self.kwargs(
                ctx,
                fitsidifile=[cfg.path(f) for f in cfg.fitsidi_files],
                vis=ctx.vis, constobsid=True, scanreindexgap_s=15.0))
        if not os.path.exists(ctx.vis):
            raise RuntimeError(f"importfitsidi did not produce {ctx.vis}")
        # TODO: the notebook's check for '<vis>.flagversions' is an ALMA
        # leftover; confirm whether importfitsidi writes it before restoring.
        # TODO: attach ANTAB Tsys/gain-curve info here once the import tool
        # (e.g. casavlbitools) is chosen.

        listfile = ctx.vis_pre + ".listobs"
        if os.path.exists(listfile):
            os.remove(listfile)
        casa.listobs(vis=ctx.vis, listfile=listfile)

        ctx.refant = self._choose_refant(ctx)
        casa.log(f"Reference antenna(s): {ctx.refant}")
        # TODO: pick good time ranges for delay and bandpass calibration.

    @staticmethod
    def _choose_refant(ctx) -> str:
        if ctx.config.refant != "auto":
            return ctx.config.refant
        coverage = ctx.casa.antenna_coverage(ctx.vis)
        return ",".join(rank_refants(coverage))
