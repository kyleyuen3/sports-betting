import pytest

from sports_betting.cli import main

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
