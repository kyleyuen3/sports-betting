"""Arbitrage ("arb" / "surebet") detection across bookmakers.

An arbitrage opportunity exists for a set of mutually exclusive outcomes
(e.g. Team A wins / Team B wins, or Win / Draw / Lose) when the sum of the
best available implied probabilities across bookmakers is less than 1 -
meaning you can back every outcome with different bookmakers and lock in
a profit regardless of the result.
"""

from __future__ import annotations

from dataclasses import dataclass

from .odds import decimal_to_implied_probability


@dataclass(frozen=True)
class ArbitrageResult:
    is_arbitrage: bool
    total_implied_probability: float
    profit_margin: float  # e.g. 0.03 == 3% guaranteed return on total stake


def find_arbitrage(best_decimal_odds: list[float]) -> ArbitrageResult:
    """Check whether the best available decimal odds for each outcome of a
    mutually exclusive market constitute an arbitrage opportunity.

    ``best_decimal_odds`` should contain one entry per outcome, each being
    the best (highest) decimal odds found for that outcome across all
    bookmakers being compared.
    """
    if not best_decimal_odds:
        raise ValueError("best_decimal_odds must be non-empty")

    total_implied = sum(decimal_to_implied_probability(o) for o in best_decimal_odds)
    is_arb = total_implied < 1.0
    margin = (1.0 / total_implied - 1.0) if is_arb else 0.0
    return ArbitrageResult(
        is_arbitrage=is_arb,
        total_implied_probability=total_implied,
        profit_margin=margin,
    )


def arbitrage_stakes(best_decimal_odds: list[float], total_stake: float) -> list[float]:
    """Compute how much to stake on each outcome to distribute ``total_stake``
    across a guaranteed arbitrage, such that the payout is equal no matter
    which outcome wins.

    Each stake is proportional to that outcome's implied probability:
    stake_i = total_stake * implied_probability_i / sum(implied_probabilities)
    """
    if total_stake <= 0:
        raise ValueError("total_stake must be positive")
    if not best_decimal_odds:
        raise ValueError("best_decimal_odds must be non-empty")

    implied = [decimal_to_implied_probability(o) for o in best_decimal_odds]
    total_implied = sum(implied)
    return [total_stake * p / total_implied for p in implied]
