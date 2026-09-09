import pytest

from sports_betting.player_props import (
    PlayerGameLog,
    PlayerProp,
    PropResult,
    append_game_log,
    compare_props,
    history_vs_opponent,
    load_game_logs_csv,
    load_props_csv,
    remove_prop,
    result_for_game,
    upsert_prop,
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


def test_append_game_log_creates_file(tmp_path):
    path = tmp_path / "logs.csv"
    log = PlayerGameLog("Josh Allen", "BUF", "MIA", "2025-09-14", "passing_yards", 278)
    append_game_log(path, log)

    logs = load_game_logs_csv(path)
    assert logs == [log]


def test_append_game_log_adds_to_existing_file(tmp_path):
    path = tmp_path / "logs.csv"
    first = PlayerGameLog("Josh Allen", "BUF", "MIA", "2025-09-14", "passing_yards", 278)
    second = PlayerGameLog("Josh Allen", "BUF", "NYJ", "2025-09-21", "passing_yards", 210)
    append_game_log(path, first)
    append_game_log(path, second)

    logs = load_game_logs_csv(path)
    assert logs == [first, second]


def test_upsert_prop_adds_new_file(tmp_path):
    path = tmp_path / "props.csv"
    prop = PlayerProp("Josh Allen", "BUF", "MIA", "passing_yards", 245.5)
    replaced = upsert_prop(path, prop)

    assert replaced is False
    assert load_props_csv(path) == [prop]


def test_upsert_prop_replaces_matching_line(tmp_path):
    path = tmp_path / "props.csv"
    original = PlayerProp("Josh Allen", "BUF", "MIA", "passing_yards", 245.5)
    updated = PlayerProp("Josh Allen", "BUF", "MIA", "passing_yards", 251.5)
    upsert_prop(path, original)
    replaced = upsert_prop(path, updated)

    assert replaced is True
    props = load_props_csv(path)
    assert props == [updated]  # replaced in place, not duplicated


def test_upsert_prop_appends_distinct_matchup(tmp_path):
    path = tmp_path / "props.csv"
    allen_vs_mia = PlayerProp("Josh Allen", "BUF", "MIA", "passing_yards", 245.5)
    allen_vs_nyj = PlayerProp("Josh Allen", "BUF", "NYJ", "passing_yards", 230.5)
    upsert_prop(path, allen_vs_mia)
    upsert_prop(path, allen_vs_nyj)

    props = load_props_csv(path)
    assert props == [allen_vs_mia, allen_vs_nyj]


def test_remove_prop_removes_matching_line(tmp_path):
    path = tmp_path / "props.csv"
    prop = PlayerProp("Josh Allen", "BUF", "MIA", "passing_yards", 245.5)
    upsert_prop(path, prop)

    removed = remove_prop(path, "Josh Allen", "BUF", "MIA", "passing_yards")
    assert removed is True
    assert load_props_csv(path) == []


def test_remove_prop_no_match_returns_false(tmp_path):
    path = tmp_path / "props.csv"
    upsert_prop(path, PlayerProp("Josh Allen", "BUF", "MIA", "passing_yards", 245.5))

    removed = remove_prop(path, "Nobody", "XXX", "YYY", "points")
    assert removed is False
    assert len(load_props_csv(path)) == 1
