"""sports_betting: odds math, EV, Kelly staking, arbitrage, and bankroll tracking."""

from .odds import (
    american_to_decimal,
    decimal_to_american,
    decimal_to_implied_probability,
    implied_probability_to_decimal,
    fractional_to_decimal,
    decimal_to_fractional,
    remove_vig,
)
from .ev import expected_value, is_positive_ev
from .kelly import kelly_fraction, kelly_stake
from .arbitrage import find_arbitrage, arbitrage_stakes
from .bankroll import Bankroll, Bet

__all__ = [
    "american_to_decimal",
    "decimal_to_american",
    "decimal_to_implied_probability",
    "implied_probability_to_decimal",
    "fractional_to_decimal",
    "decimal_to_fractional",
    "remove_vig",
    "expected_value",
    "is_positive_ev",
    "kelly_fraction",
    "kelly_stake",
    "find_arbitrage",
    "arbitrage_stakes",
    "Bankroll",
    "Bet",
]

__version__ = "0.1.0"
