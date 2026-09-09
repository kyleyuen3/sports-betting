import pytest

from sports_betting.player_props import (
    PlayerGameLog,
    PlayerProp,
    PropResult,
    compare_props,
    history_vs_opponent,
    load_game_logs_csv,
    load_props_csv,
    result_for_game,
)

GAME_LOGS = [
    PlayerGameLog("Josh Allen", "BUF", "MIA", "2024-09-01", "passing_yards", 300),
    PlayerGameLog("Josh Allen", "BUF", "MIA", "2024-12-01", "passing_yards", 200),
    PlayerGameLog("Josh Allen", "BUF", "NYJ", "2024-10-01", "passing_yards", 260),
    PlayerGameLog("Josh Allen", "BUF", "MIA", "2023-09-01", "rushing_yards", 50),
    PlayerGameLog("Stefon Diggs", "HOU", "MIA", "2024-09-01", "receiving_yards", 90),
]


def test_result_for_game():
    game = PlayerGameLog("P", "T", "OPP", "2024-01-01", "points", 25)
    assert result_for_game(game, 20) == PropResult.OVER
    assert result_for_game(game, 30) == PropResult.UNDER
    assert result_for_game(game, 25) == PropResult.PUSH


def test_history_vs_opponent_filters_by_player_opponent_and_stat():
    prop = PlayerProp("Josh Allen", "BUF", "MIA", "passing_yards", 245.5)
    result = history_vs_opponent(prop, GAME_LOGS)

    # Only the two passing_yards games vs MIA should match (not the NYJ game,
    # not the rushing_yards game vs MIA, not Diggs' game).
    assert result.games_played == 2
    assert result.overs == 1  # 300 > 245.5
    assert result.unders == 1  # 200 < 245.5
    assert result.pushes == 0
    assert result.hit_rate_over == pytest.approx(0.5)
    assert result.average_stat == pytest.approx(250.0)


def test_history_vs_opponent_no_matches():
    prop = PlayerProp("Nobody", "XXX", "YYY", "points", 10)
    result = history_vs_opponent(prop, GAME_LOGS)
    assert result.games_played == 0
    assert result.hit_rate_over is None
    assert result.average_stat is None
    assert result.overs == 0


def test_compare_props_filters_by_team():
    props = [
        PlayerProp("Josh Allen", "BUF", "MIA", "passing_yards", 245.5),
        PlayerProp("Stefon Diggs", "HOU", "MIA", "receiving_yards", 70.5),
    ]
    buf_only = compare_props(props, GAME_LOGS, team="BUF")
    assert len(buf_only) == 1
    assert buf_only[0].prop.player == "Josh Allen"

    all_results = compare_props(props, GAME_LOGS)
    assert len(all_results) == 2


def test_load_props_csv(tmp_path):
    csv_path = tmp_path / "props.csv"
    csv_path.write_text(
        "player,team,opponent,stat_type,line\n"
        "Josh Allen,BUF,MIA,passing_yards,245.5\n"
    )
    props = load_props_csv(csv_path)
    assert len(props) == 1
    assert props[0] == PlayerProp("Josh Allen", "BUF", "MIA", "passing_yards", 245.5)


def test_load_game_logs_csv(tmp_path):
    csv_path = tmp_path / "logs.csv"
    csv_path.write_text(
        "player,team,opponent,date,stat_type,stat_value\n"
        "Josh Allen,BUF,MIA,2024-09-01,passing_yards,300\n"
    )
    logs = load_game_logs_csv(csv_path)
    assert len(logs) == 1
    assert logs[0] == PlayerGameLog("Josh Allen", "BUF", "MIA", "2024-09-01", "passing_yards", 300.0)


def test_load_props_csv_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_props_csv(tmp_path / "missing.csv")
