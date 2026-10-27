import pytest

from vlbapipe.heuristics.opacity import classify_regime
from vlbapipe.heuristics.refant import rank_refants


def test_refant_ranking():
    cov = {"KP": 10, "PT": 98, "FD": 100, "LA": 98}
    assert rank_refants(cov) == ["FD", "LA", "PT"]


def test_refant_empty():
    with pytest.raises(ValueError):
        rank_refants({})


@pytest.mark.parametrize("f,r", [(None, "unset"), (1.6, "ionosphere"),
                                 (8.4, "unresolved"), (22.0, "troposphere")])
def test_regime(f, r):
    assert classify_regime(f) == r


from vlbapipe.heuristics.imaging import beam_mas, optimal_imsize, tclean_params


def test_optimal_imsize():
    assert optimal_imsize(640) == 640
    assert optimal_imsize(641) == 648
    assert optimal_imsize(10) == 64


def test_tclean_params_vlba_cband():
    # ~8600 km baseline at 5.26 GHz -> ~1.4 mas beam
    p = tclean_params(8.6e6, 5.26e9, min_freq_hz=5.0e9)
    assert 1.3 < beam_mas(8.6e6 * 5.26e9 / 299792458.0) < 1.45
    assert p["cell"][0].endswith("mas")
    assert p["imsize"][0] == p["imsize"][1] >= 640
    assert p["deconvolver"] == "hogbom"


def test_tclean_params_wideband_uses_mtmfs():
    p = tclean_params(8.6e6, 2.0e9, min_freq_hz=1.0e9)
    assert p["deconvolver"] == "mtmfs" and p["nterms"] == 2


def test_tclean_params_imsize_capped():
    p = tclean_params(8.6e6, 43e9, fov_mas=1e5, max_imsize=2048)
    assert p["imsize"] == [2048, 2048]
