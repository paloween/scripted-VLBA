"""Which atmospheric correction applies at a given observing frequency."""
from __future__ import annotations

IONOSPHERE_BELOW_GHZ = 4.5
TROPOSPHERE_ABOVE_GHZ = 15.0


def classify_regime(obs_freq_ghz: float | None) -> str:
    """'ionosphere', 'troposphere', 'unresolved' (4.5-15 GHz) or 'unset'."""
    if obs_freq_ghz is None:
        return "unset"
    if obs_freq_ghz < IONOSPHERE_BELOW_GHZ:
        return "ionosphere"
    if obs_freq_ghz >= TROPOSPHERE_ABOVE_GHZ:
        return "troposphere"
    return "unresolved"
