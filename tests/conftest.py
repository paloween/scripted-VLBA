import os

import pytest

from vlbapipe.casa_api import CasaAPI
from vlbapipe.config import Config


class FakeCasa:
    """Stands in for casatasks: records nothing itself, creates output files."""

    class casalog:
        @staticmethod
        def post(*a, **k):
            pass

    def importfitsidi(self, vis, **k):
        os.makedirs(vis)

    def gencal(self, caltable, **k):
        os.makedirs(caltable)

    def accor(self, caltable, **k):
        os.makedirs(caltable)

    def smoothcal(self, caltable, **k):
        os.makedirs(caltable)

    def listobs(self, listfile, **k):
        open(listfile, "w").close()

    def flagdata(self, **k):
        pass

    def flagmanager(self, **k):
        pass


@pytest.fixture
def config(tmp_path):
    return Config(vis="t.ms", fitsidi_files=["t.idifits"], workdir=str(tmp_path),
                  calibrate_delay="3C84", observe_target="J0001", refant="FD")


@pytest.fixture
def casa():
    api = CasaAPI(backend=FakeCasa())
    api.antenna_coverage = lambda vis: {"FD": 100.0, "PT": 98.0, "KP": 10.0}
    return api
