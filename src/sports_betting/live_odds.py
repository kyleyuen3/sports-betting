"""Live odds fetching via https://the-odds-api.com/.

The Odds API aggregates real-time odds from dozens of bookmakers across
many sports. Get a free API key at https://the-odds-api.com/ (the free
tier is enough for casual use) and either pass it explicitly or set the
``ODDS_API_KEY`` environment variable.

This module only fetches and parses odds - it doesn't place bets. Parsed
odds feed directly into ``sports_betting.ev``, ``sports_betting.kelly``,
and ``sports_betting.arbitrage``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional, Protocol

DEFAULT_BASE_URL = "https://api.the-odds-api.com/v4"
DEFAULT_TIMEOUT = 10


class OddsAPIError(Exception):
    """Raised when the odds API returns an error response."""


class HTTPResponse(Protocol):
    status_code: int
    text: str

    def json(self) -> Any: ...


class HTTPSession(Protocol):
    def get(self, url: str, params: dict, timeout: float) -> HTTPResponse: ...


@dataclass(frozen=True)
class Outcome:
    """A single betting outcome (e.g. one team to win) and its price."""

    name: str
    price: float  # decimal odds


@dataclass(frozen=True)
class BookmakerOdds:
    """Odds offered by one bookmaker for a game's outcomes."""

    key: str
    title: str
    outcomes: list[Outcome]


@dataclass(frozen=True)
class GameOdds:
    """Odds for a single game, aggregated across bookmakers."""

    id: str
    sport_key: str
    commence_time: str
    home_team: str
    away_team: str
    bookmakers: list[BookmakerOdds]

    def best_odds_by_outcome(self) -> dict[str, tuple[float, str]]:
        """The best (highest) decimal odds for each outcome name, and which
        bookmaker offered it. Useful for both finding the most profitable
        single bet and checking for arbitrage across bookmakers.
        """
        best: dict[str, tuple[float, str]] = {}
        for bookmaker in self.bookmakers:
            for outcome in bookmaker.outcomes:
                current = best.get(outcome.name)
                if current is None or outcome.price > current[0]:
                    best[outcome.name] = (outcome.price, bookmaker.title)
        return best


class OddsAPIClient:
    """Thin client for The Odds API's REST endpoints.

    A custom ``session`` (anything with a ``requests.Session``-shaped
    ``.get(url, params=, timeout=)`` method) can be injected for testing
    without hitting the network.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        session: Optional[HTTPSession] = None,
    ):
        self.api_key = api_key or os.environ.get("ODDS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "An API key is required: pass api_key=... or set the "
                "ODDS_API_KEY environment variable. Get a free key at "
                "https://the-odds-api.com/"
            )
        self.base_url = base_url.rstrip("/")
        if session is None:
            import requests  # imported lazily so the module loads without the dependency installed

            session = requests.Session()
        self._session = session

    def _get(self, path: str, **params: Any) -> Any:
        query = {"apiKey": self.api_key, **params}
        response = self._session.get(
            f"{self.base_url}{path}", params=query, timeout=DEFAULT_TIMEOUT
        )
        if response.status_code != 200:
            raise OddsAPIError(
                f"Odds API request to {path} failed "
                f"({response.status_code}): {response.text[:300]}"
            )
        return response.json()

    def list_sports(self) -> list[dict]:
        """List available sport keys (e.g. "basketball_nba", "soccer_epl")."""
        return self._get("/sports")

    def get_odds(
        self,
        sport_key: str,
        regions: str = "us",
        markets: str = "h2h",
        odds_format: str = "decimal",
    ) -> list[GameOdds]:
        """Fetch current odds for all upcoming games in a sport.

        ``regions`` selects which bookmakers to include (e.g. "us", "uk",
        "eu", "au", comma-separated for more than one). ``markets`` selects
        bet types (e.g. "h2h" for moneyline, "spreads", "totals").
        """
        raw_games = self._get(
            f"/sports/{sport_key}/odds",
            regions=regions,
            markets=markets,
            oddsFormat=odds_format,
        )
        return [_parse_game(g) for g in raw_games]


def _parse_game(data: dict) -> GameOdds:
    bookmakers = [
        BookmakerOdds(
            key=bm["key"],
            title=bm["title"],
            outcomes=[
                Outcome(name=outcome["name"], price=float(outcome["price"]))
                for market in bm.get("markets", [])
                for outcome in market.get("outcomes", [])
            ],
        )
        for bm in data.get("bookmakers", [])
    ]
    return GameOdds(
        id=data["id"],
        sport_key=data["sport_key"],
        commence_time=data["commence_time"],
        home_team=data["home_team"],
        away_team=data["away_team"],
        bookmakers=bookmakers,
    )


def scan_for_arbitrage(games: list[GameOdds]):
    """Check a list of live games for arbitrage opportunities.

    Returns a list of ``(game, ArbitrageResult)`` pairs, one per game that
    has best-odds arbitrage across the bookmakers included in that game's
    data - in the order the games were given.
    """
    from .arbitrage import find_arbitrage  # local import avoids a cycle at module load time

    results = []
    for game in games:
        best = game.best_odds_by_outcome()
        if len(best) < 2:
            continue  # need at least two outcomes to check for arbitrage
        prices = [price for price, _bookmaker in best.values()]
        result = find_arbitrage(prices)
        if result.is_arbitrage:
            results.append((game, result))
    return results
