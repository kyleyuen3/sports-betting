import pytest

from sports_betting.live_odds import (
    GameOdds,
    OddsAPIClient,
    OddsAPIError,
    scan_for_arbitrage,
)


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        return self._json_data


class FakeSession:
    """Records the last request and returns a canned response."""

    def __init__(self, response: FakeResponse):
        self.response = response
        self.last_url = None
        self.last_params = None

    def get(self, url, params, timeout):
        self.last_url = url
        self.last_params = params
        self.last_timeout = timeout
        return self.response


RAW_GAME = {
    "id": "game1",
    "sport_key": "basketball_nba",
    "commence_time": "2026-01-01T00:00:00Z",
    "home_team": "Home Team",
    "away_team": "Away Team",
    "bookmakers": [
        {
            "key": "bookA",
            "title": "Book A",
            "markets": [
                {
                    "key": "h2h",
                    "outcomes": [
                        {"name": "Home Team", "price": 1.91},
                        {"name": "Away Team", "price": 2.10},
                    ],
                }
            ],
        },
        {
            "key": "bookB",
            "title": "Book B",
            "markets": [
                {
                    "key": "h2h",
                    "outcomes": [
                        {"name": "Home Team", "price": 2.05},
                        {"name": "Away Team", "price": 1.80},
                    ],
                }
            ],
        },
    ],
}


def test_requires_api_key(monkeypatch):
    monkeypatch.delenv("ODDS_API_KEY", raising=False)
    with pytest.raises(ValueError):
        OddsAPIClient(session=FakeSession(FakeResponse()))


def test_api_key_from_env(monkeypatch):
    monkeypatch.setenv("ODDS_API_KEY", "env-key")
    client = OddsAPIClient(session=FakeSession(FakeResponse(json_data=[])))
    assert client.api_key == "env-key"


def test_list_sports_sends_api_key():
    session = FakeSession(FakeResponse(json_data=[{"key": "basketball_nba"}]))
    client = OddsAPIClient(api_key="test-key", session=session)
    sports = client.list_sports()
    assert sports == [{"key": "basketball_nba"}]
    assert session.last_params["apiKey"] == "test-key"
    assert session.last_url.endswith("/sports")


def test_get_odds_parses_games():
    session = FakeSession(FakeResponse(json_data=[RAW_GAME]))
    client = OddsAPIClient(api_key="test-key", session=session)
    games = client.get_odds("basketball_nba")

    assert len(games) == 1
    game = games[0]
    assert isinstance(game, GameOdds)
    assert game.home_team == "Home Team"
    assert game.away_team == "Away Team"
    assert len(game.bookmakers) == 2
    assert session.last_params["regions"] == "us"
    assert session.last_params["markets"] == "h2h"
    assert session.last_params["oddsFormat"] == "decimal"


def test_get_odds_passes_through_options():
    session = FakeSession(FakeResponse(json_data=[]))
    client = OddsAPIClient(api_key="test-key", session=session)
    client.get_odds("soccer_epl", regions="uk", markets="spreads", odds_format="american")
    assert session.last_params["regions"] == "uk"
    assert session.last_params["markets"] == "spreads"
    assert session.last_params["oddsFormat"] == "american"


def test_error_response_raises():
    session = FakeSession(FakeResponse(status_code=401, text="bad key"))
    client = OddsAPIClient(api_key="wrong-key", session=session)
    with pytest.raises(OddsAPIError):
        client.list_sports()


def test_best_odds_by_outcome():
    session = FakeSession(FakeResponse(json_data=[RAW_GAME]))
    client = OddsAPIClient(api_key="test-key", session=session)
    game = client.get_odds("basketball_nba")[0]

    best = game.best_odds_by_outcome()
    assert best["Home Team"] == (2.05, "Book B")
    assert best["Away Team"] == (2.10, "Book A")


def test_scan_for_arbitrage_finds_opportunity():
    session = FakeSession(FakeResponse(json_data=[RAW_GAME]))
    client = OddsAPIClient(api_key="test-key", session=session)
    games = client.get_odds("basketball_nba")

    # Best odds: Home 2.05, Away 2.10 -> implied 0.4878 + 0.4762 = 0.964 < 1
    opportunities = scan_for_arbitrage(games)
    assert len(opportunities) == 1
    game, result = opportunities[0]
    assert game.id == "game1"
    assert result.is_arbitrage is True
    assert result.profit_margin > 0


def test_scan_for_arbitrage_no_opportunity():
    no_arb_game = {
        **RAW_GAME,
        "bookmakers": [
            {
                "key": "bookA",
                "title": "Book A",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Home Team", "price": 1.80},
                            {"name": "Away Team", "price": 1.80},
                        ],
                    }
                ],
            }
        ],
    }
    session = FakeSession(FakeResponse(json_data=[no_arb_game]))
    client = OddsAPIClient(api_key="test-key", session=session)
    games = client.get_odds("basketball_nba")
    assert scan_for_arbitrage(games) == []
