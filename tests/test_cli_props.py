import pytest

from sports_betting.cli import main
from sports_betting.player_props import load_game_logs_csv, load_props_csv

PROPS_CSV = (
    "player,team,opponent,stat_type,line\n"
    "Josh Allen,BUF,MIA,passing_yards,245.5\n"
    "Stefon Diggs,HOU,MIA,receiving_yards,70.5\n"
)

LOGS_CSV = (
    "player,team,opponent,date,stat_type,stat_value\n"
    "Josh Allen,BUF,MIA,2024-09-01,passing_yards,300\n"
    "Josh Allen,BUF,MIA,2024-12-01,passing_yards,200\n"
    "Stefon Diggs,HOU,MIA,2024-09-01,receiving_yards,90\n"
)


def _write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content)
    return path


def test_compare_prints_all_props(tmp_path, capsys):
    props_path = _write(tmp_path, "props.csv", PROPS_CSV)
    logs_path = _write(tmp_path, "logs.csv", LOGS_CSV)

    main(["props", "compare", "--props", str(props_path), "--logs", str(logs_path)])
    out = capsys.readouterr().out
    assert "Josh Allen" in out
    assert "Stefon Diggs" in out


def test_compare_filters_by_team(tmp_path, capsys):
    props_path = _write(tmp_path, "props.csv", PROPS_CSV)
    logs_path = _write(tmp_path, "logs.csv", LOGS_CSV)

    main(["props", "compare", "--props", str(props_path), "--logs", str(logs_path), "--team", "BUF"])
    out = capsys.readouterr().out
    assert "Josh Allen" in out
    assert "Stefon Diggs" not in out


def test_compare_shows_hit_rate_and_average(tmp_path, capsys):
    props_path = _write(tmp_path, "props.csv", PROPS_CSV)
    logs_path = _write(tmp_path, "logs.csv", LOGS_CSV)

    main(["props", "compare", "--props", str(props_path), "--logs", str(logs_path), "--team", "BUF"])
    out = capsys.readouterr().out
    assert "50%" in out  # 1 of 2 games over 245.5
    assert "250" in out  # average of 300 and 200


def test_compare_missing_props_file_exits(tmp_path):
    logs_path = _write(tmp_path, "logs.csv", LOGS_CSV)
    with pytest.raises(SystemExit):
        main(["props", "compare", "--props", str(tmp_path / "missing.csv"), "--logs", str(logs_path)])


def test_compare_no_match_for_unknown_team(tmp_path, capsys):
    props_path = _write(tmp_path, "props.csv", PROPS_CSV)
    logs_path = _write(tmp_path, "logs.csv", LOGS_CSV)

    main(["props", "compare", "--props", str(props_path), "--logs", str(logs_path), "--team", "ZZZ"])
    assert "No props matched." in capsys.readouterr().out


def test_props_log_appends_game(tmp_path, capsys):
    logs_path = tmp_path / "logs.csv"
    main(
        [
            "props", "log",
            "--player", "Josh Allen", "--team", "BUF", "--opponent", "MIA",
            "--date", "2025-09-14", "--stat-type", "passing_yards", "--value", "278",
            "--logs", str(logs_path),
        ]
    )
    out = capsys.readouterr().out
    assert "Josh Allen" in out
    logs = load_game_logs_csv(logs_path)
    assert len(logs) == 1
    assert logs[0].stat_value == 278


def test_props_set_line_adds_then_updates(tmp_path, capsys):
    props_path = tmp_path / "props.csv"
    main(
        [
            "props", "set-line",
            "--player", "Josh Allen", "--team", "BUF", "--opponent", "NYJ",
            "--stat-type", "passing_yards", "--line", "230.5",
            "--props", str(props_path),
        ]
    )
    assert "Added line" in capsys.readouterr().out
    assert load_props_csv(props_path)[0].line == 230.5

    main(
        [
            "props", "set-line",
            "--player", "Josh Allen", "--team", "BUF", "--opponent", "NYJ",
            "--stat-type", "passing_yards", "--line", "251.5",
            "--props", str(props_path),
        ]
    )
    out = capsys.readouterr().out
    assert "Updated line" in out
    props = load_props_csv(props_path)
    assert len(props) == 1
    assert props[0].line == 251.5


def test_props_remove_line(tmp_path, capsys):
    props_path = tmp_path / "props.csv"
    main(
        [
            "props", "set-line",
            "--player", "Josh Allen", "--team", "BUF", "--opponent", "MIA",
            "--stat-type", "passing_yards", "--line", "245.5",
            "--props", str(props_path),
        ]
    )
    capsys.readouterr()

    main(
        [
            "props", "remove-line",
            "--player", "Josh Allen", "--team", "BUF", "--opponent", "MIA",
            "--stat-type", "passing_yards", "--props", str(props_path),
        ]
    )
    assert "Removed line" in capsys.readouterr().out
    assert load_props_csv(props_path) == []


def test_props_remove_line_no_match_exits(tmp_path):
    props_path = tmp_path / "props.csv"
    main(
        [
            "props", "set-line",
            "--player", "Josh Allen", "--team", "BUF", "--opponent", "MIA",
            "--stat-type", "passing_yards", "--line", "245.5",
            "--props", str(props_path),
        ]
    )
    with pytest.raises(SystemExit):
        main(
            [
                "props", "remove-line",
                "--player", "Nobody", "--team", "XXX", "--opponent", "YYY",
                "--stat-type", "points", "--props", str(props_path),
            ]
        )
