"""Reference-antenna selection. Pure Python so it can be tested without CASA."""
from __future__ import annotations


def rank_refants(seconds_on_source: dict[str, float], n: int = 3,
                 min_fraction: float = 0.9) -> list[str]:
    """Antennas present for most of the observation, best-covered first.

    Keeps antennas with at least ``min_fraction`` of the best antenna's time,
    at most ``n`` of them. Ties break alphabetically for reproducibility.
    """
    if not seconds_on_source:
        raise ValueError("no antenna coverage information")
    best = max(seconds_on_source.values())
    if best <= 0:
        raise ValueError("no antenna has any on-source time")
    ranked = sorted(seconds_on_source.items(), key=lambda kv: (-kv[1], kv[0]))
    return [a for a, s in ranked if s >= min_fraction * best][:n]
