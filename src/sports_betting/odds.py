"""Conversions between odds formats and implied probability.

Supported formats:
- American (moneyline), e.g. +150, -200
- Decimal (European), e.g. 2.50, 1.50
- Fractional (UK), e.g. "3/2", "1/2"

All functions operate on decimal odds internally since that is the
easiest representation for arithmetic (payout multiplier including stake).
"""

from __future__ import annotations

from fractions import Fraction


def american_to_decimal(american: float) -> float:
    """Convert American odds (e.g. +150, -200) to decimal odds."""
    if american == 0:
        raise ValueError("American odds cannot be 0")
    if american > 0:
        return 1.0 + american / 100.0
    return 1.0 + 100.0 / abs(american)


def decimal_to_american(decimal: float) -> float:
    """Convert decimal odds (e.g. 2.5) to American odds."""
    if decimal <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    if decimal >= 2:
        return (decimal - 1) * 100.0
    return -100.0 / (decimal - 1)


def fractional_to_decimal(fractional: str) -> float:
    """Convert fractional odds (e.g. "3/2", "5/1") to decimal odds."""
    frac = Fraction(fractional)
    if frac <= 0:
        raise ValueError("Fractional odds must be positive")
    return 1.0 + float(frac)


def decimal_to_fractional(decimal: float) -> str:
    """Convert decimal odds to a simplified fractional odds string."""
    if decimal <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    frac = Fraction(decimal - 1).limit_denominator(100)
    return f"{frac.numerator}/{frac.denominator}"


def decimal_to_implied_probability(decimal: float) -> float:
    """Convert decimal odds to the implied win probability (includes the vig)."""
    if decimal <= 1:
        raise ValueError("Decimal odds must be greater than 1")
    return 1.0 / decimal


def implied_probability_to_decimal(probability: float) -> float:
    """Convert an implied win probability to decimal odds."""
    if not 0 < probability <= 1:
        raise ValueError("Probability must be in (0, 1]")
    return 1.0 / probability


def remove_vig(decimal_odds: list[float]) -> list[float]:
    """Normalize a list of decimal odds for a mutually exclusive market
    (e.g. all outcomes of a moneyline) to remove the bookmaker's margin (vig),
    returning "fair" (no-vig) win probabilities that sum to 1.
    """
    if not decimal_odds:
        raise ValueError("decimal_odds must be non-empty")
    implied = [decimal_to_implied_probability(o) for o in decimal_odds]
    total = sum(implied)
    if total <= 0:
        raise ValueError("Implied probabilities must sum to a positive value")
    return [p / total for p in implied]
