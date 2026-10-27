"""Notebook steps 2-5: a priori flagging and a priori calibration tables."""
from __future__ import annotations

import os
import shutil
import subprocess

from ..heuristics.opacity import classify_regime
from .base import Stage

EOP_URL = ("ftp://gdc.cddis.eosdis.nasa.gov/vlbi/gsfc/ancillary/"
           "solve_apriori/usno_finals.erp")


def _rm(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)


class PriorCals(Stage):
    name = "priorcals"
    order = 1
    requires = ("importdata",)

    def run(self, ctx):
        self._flag(ctx)
        self._eop_and_atmosphere(ctx)
        self._amplitude_priors(ctx)
        self._antpos(ctx)

    # -- step 2 ---------------------------------------------------------
    def _flag(self, ctx):
        cfg, casa = ctx.config, ctx.casa
        q = cfg.quack_interval_s
        for mode in ("beg", "endb"):
            casa.flagdata(vis=ctx.vis, mode="quack", quackinterval=q,
                          quackmode=mode, quackincrement=True)
        if cfg.tfcrop:
            # The notebook ran tfcrop twice (calculate, then apply); one apply
            # call does the same work.
            casa.flagdata(vis=ctx.vis, mode="tfcrop", datacolumn="data",
                          timecutoff=4.0, freqcutoff=3.0, flagdimension="time",
                          action="apply", display="none")
        if cfg.manual_flags:
            casa.flagdata(vis=ctx.vis, mode="manual", spw=cfg.manual_flag_spw,
                          flagbackup=False)
        casa.flagmanager(vis=ctx.vis, mode="save", versionname="AprioriFlags")

    # -- step 3 ---------------------------------------------------------
    def _eop_and_atmosphere(self, ctx):
        casa = ctx.casa
        eop_file = ctx.config.path("usno_finals.erp")
        _rm(eop_file)
        # list-form subprocess: no shell, no credentials embedded in a command line string
        subprocess.run(["curl", "-f", "-u", "anonymous:dummy@gmail.com",
                        "--ftp-ssl", EOP_URL, "-o", eop_file], check=False)
        if not os.path.exists(eop_file):
            ctx.warn("Could not download the EOP file; skipping EOP correction.")
        else:
            table = ctx.vis_pre + ".eop"
            _rm(table)
            casa.gencal(vis=ctx.vis, caltable=table, caltype="eop", infile=eop_file)
            self.add_table(ctx, table, "nearest", kind="eop")

        regime = classify_regime(ctx.config.obs_freq_ghz)
        if regime == "ionosphere":
            ctx.warn("Ionospheric regime (<4.5 GHz): tecim table not yet wired up.")
        elif regime == "troposphere":
            ctx.warn("Tropospheric regime (>=15 GHz): no opacity term available.")
        else:
            ctx.warn(f"Atmospheric regime '{regime}': no opacity/ionosphere "
                     "correction applied.")

    # -- step 4 ---------------------------------------------------------
    def _amplitude_priors(self, ctx):
        casa = ctx.casa
        accor_tab = ctx.vis_pre + ".accor"
        smooth_tab = ctx.vis_pre + "_smooth.accor"
        tsys_tab = ctx.vis_pre + ".tsys"
        gc_tab = ctx.vis_pre + ".gcal"
        for t in (accor_tab, smooth_tab, tsys_tab, gc_tab):
            _rm(t)

        # NOTE: EVN data need Tsys and gain curves appended to the FITS-IDI
        # from the ANTAB file before import.
        casa.accor(**self.kwargs(
            ctx, vis=ctx.vis, caltable=accor_tab, solint="30s",
            gaintable=ctx.registry.gaintables(before_order=self.order + 1),
            interp=ctx.registry.interp(before_order=self.order + 1)))
        casa.smoothcal(vis=ctx.vis, tablein=accor_tab, caltable=smooth_tab,
                       smoothtype="median", smoothtime=1800.0)
        self.add_table(ctx, smooth_tab, "nearest", kind="accor")

        casa.gencal(vis=ctx.vis, caltable=tsys_tab, caltype="tsys", uniform=False)
        casa.gencal(vis=ctx.vis, caltable=gc_tab, caltype="gc")
        # Apply order matches the notebook: gain curve, then Tsys.
        self.add_table(ctx, gc_tab, "nearest", kind="gc")
        self.add_table(ctx, tsys_tab, "nearest", kind="tsys")
        # TODO: plotting; automated flagging of extreme Tsys solutions.

    # -- step 5 ---------------------------------------------------------
    def _antpos(self, ctx):
        if not ctx.config.antpos:
            return
        table = ctx.vis_pre + ".antpos"
        _rm(table)
        ctx.casa.gencal(vis=ctx.vis, caltable=table, caltype="antpos")
        self.add_table(ctx, table, "nearest", kind="antpos")
