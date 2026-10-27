"""tclean parameters from uv coverage. Pure Python so it can be tested without CASA."""
from __future__ import annotations

import math

C_M_PER_S = 299792458.0
RAD_TO_MAS = 180.0 / math.pi * 3600.0 * 1000.0

# Above this fractional bandwidth the source spectral index matters across
# the band, so switch to multi-term MFS.
MTMFS_ABOVE_FRACTIONAL_BW = 0.10

# auto-multithresh settings recommended for sparse, long-baseline arrays
# (CASA guide values for ALMA long baselines; VLBA uv coverage is sparser
# still, so these are a starting point, not tuned). The initial mask threshold
# is sidelobethreshold * sidelobe level * peak; VLBA dirty beams have sidelobes
# of ~0.4-0.6, so the ALMA value of 3.0 masks nothing (seen on TL016B).
AUTOMASK_LONG_BASELINE = {
    "sidelobethreshold": 1.0,
    "noisethreshold": 5.0,
    "lownoisethreshold": 1.5,
    "minbeamfrac": 0.3,
    "negativethreshold": 0.0,
}


def beam_mas(max_uv_lambda: float) -> float:
    """Approximate synthesized beam (lambda / B_max) in milliarcseconds."""
    if max_uv_lambda <= 0:
        raise ValueError("max_uv_lambda must be positive")
    return RAD_TO_MAS / max_uv_lambda


def optimal_imsize(n: int, minimum: int = 64) -> int:
    """Smallest even size >= n whose prime factors are only 2, 3, 5 (FFT-friendly)."""
    n = max(int(math.ceil(n)), minimum)
    while True:
        if n % 2 == 0:
            m = n
            for p in (2, 3, 5):
                while m % p == 0:
                    m //= p
            if m == 1:
                return n
        n += 1


def tclean_params(max_uvdist_m: float, max_freq_hz: float,
                  min_freq_hz: float | None = None,
                  pixels_per_beam: float = 5.0, fov_beams: float = 128.0,
                  fov_mas: float | None = None, max_imsize: int = 4096,
                  nsigma: float = 3.0, niter: int = 1000) -> dict:
    """tclean keyword arguments for a compact source at the phase centre.

    The cell samples the beam at the highest frequency with ``pixels_per_beam``
    pixels. The field is ``fov_mas`` if given, else ``fov_beams`` beams across
    (VLBI images cannot cover the antenna primary beam). The image is capped at
    ``max_imsize`` pixels. The returned dict can be passed straight to tclean
    (add vis, field and imagename).
    """
    if max_freq_hz <= 0:
        raise ValueError("max_freq_hz must be positive")
    max_uv_lambda = max_uvdist_m * max_freq_hz / C_M_PER_S
    beam = beam_mas(max_uv_lambda)
    cell_mas = beam / pixels_per_beam

    fov = fov_mas if fov_mas is not None else fov_beams * beam
    imsize = min(optimal_imsize(fov / cell_mas), max_imsize)

    params = {
        "imsize": [imsize, imsize],
        "cell": [f"{cell_mas:.4g}mas"],
        "specmode": "mfs",
        "gridder": "standard",
        "deconvolver": "hogbom",
        "stokes": "I",
        "weighting": "natural",
        "niter": niter,
        "nsigma": nsigma,
        "usemask": "auto-multithresh",
        **AUTOMASK_LONG_BASELINE,
        "interactive": False,
    }

    if min_freq_hz is not None:
        frac_bw = (max_freq_hz - min_freq_hz) / (0.5 * (max_freq_hz + min_freq_hz))
        if frac_bw > MTMFS_ABOVE_FRACTIONAL_BW:
            params["deconvolver"] = "mtmfs"
            params["nterms"] = 2
    return params
