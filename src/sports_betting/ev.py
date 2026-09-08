"""Expected value calculations for a single bet."""

from __future__ import annotations


def expected_value(probability: float, decimal_odds: float, stake: float = 1.0) -> float:
    """Expected profit (not including the returned stake) of a bet.

    ``probability`` is your own estimate of the true win probability,
    ``decimal_odds`` is the odds offered by the bookmaker, and ``stake``
    is the amount wagered.

    EV = (probability * (decimal_odds - 1) * stake) - ((1 - probability) * stake)
    """
    if not 0 <= probability <= 1:
        raise ValueError("probability must be in [0, 1]")
    if decimal_odds <= 1:
        raise ValueError("decimal_odds must be greater than 1")
    if stake < 0:
        raise ValueError("stake must be non-negative")

    profit_if_win = (decimal_odds - 1) * stake
    loss_if_lose = stake
    return probability * profit_if_win - (1 - probability) * loss_if_lose


def ev_percentage(probability: float, decimal_odds: float) -> float:
    """Expected value as a percentage of stake (a.k.a. "edge")."""
    return expected_value(probability, decimal_odds, stake=1.0) * 100.0


def is_positive_ev(probability: float, decimal_odds: float) -> bool:
    """Whether a bet has positive expected value given your probability estimate."""
    return expected_value(probability, decimal_odds) > 0
