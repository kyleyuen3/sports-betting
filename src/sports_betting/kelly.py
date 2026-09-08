"""Kelly criterion staking calculations."""

from __future__ import annotations


def kelly_fraction(probability: float, decimal_odds: float) -> float:
    """Fraction of bankroll to stake according to the full Kelly criterion.

    f* = (b*p - q) / b

    where ``b`` is the net decimal odds (decimal_odds - 1), ``p`` is your
    win probability estimate, and ``q = 1 - p``.

    Returns 0 when the bet has no edge (negative or zero EV) rather than a
    negative fraction, since you shouldn't stake anything on a losing bet.
    """
    if not 0 <= probability <= 1:
        raise ValueError("probability must be in [0, 1]")
    if decimal_odds <= 1:
        raise ValueError("decimal_odds must be greater than 1")

    b = decimal_odds - 1
    q = 1 - probability
    f = (b * probability - q) / b
    return max(f, 0.0)


def kelly_stake(
    probability: float,
    decimal_odds: float,
    bankroll: float,
    fraction: float = 1.0,
) -> float:
    """Recommended stake in currency units.

    ``fraction`` scales the full Kelly stake (e.g. 0.5 for "half Kelly"),
    which is common practice to reduce variance since Kelly assumes exact
    knowledge of the true probability.
    """
    if bankroll < 0:
        raise ValueError("bankroll must be non-negative")
    if fraction < 0:
        raise ValueError("fraction must be non-negative")

    return kelly_fraction(probability, decimal_odds) * fraction * bankroll
