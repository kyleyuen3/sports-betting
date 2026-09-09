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
from .bankroll import Bankroll, Bet, BetOutcome, DEFAULT_BANKROLL_PATH
from .live_odds import OddsAPIClient, OddsAPIError, GameOdds, BookmakerOdds, Outcome, scan_for_arbitrage
from .player_props import (
    PlayerGameLog,
    PlayerProp,
    PropHistoryResult,
    PropResult,
    result_for_game,
    history_vs_opponent,
    compare_props,
    load_game_logs_csv,
    load_props_csv,
)

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
    "BetOutcome",
    "DEFAULT_BANKROLL_PATH",
    "OddsAPIClient",
    "OddsAPIError",
    "GameOdds",
    "BookmakerOdds",
    "Outcome",
    "scan_for_arbitrage",
    "PlayerGameLog",
    "PlayerProp",
    "PropHistoryResult",
    "PropResult",
    "result_for_game",
    "history_vs_opponent",
    "compare_props",
    "load_game_logs_csv",
    "load_props_csv",
]

__version__ = "0.1.0"
