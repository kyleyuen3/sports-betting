import pytest

from sports_betting.bankroll import Bankroll
from sports_betting.cli import main


def test_init_creates_bankroll(tmp_path, capsys):
    path = tmp_path / "bankroll.json"
    rc = main(["bankroll", "init", "--starting-balance", "1000", "--file", str(path)])
    assert rc == 0
    assert path.exists()
    out = capsys.readouterr().out
    assert "1000.00" in out


def test_init_refuses_to_overwrite_without_force(tmp_path):
    path = tmp_path / "bankroll.json"
    Bankroll(1000).save(path)
    with pytest.raises(SystemExit):
        main(["bankroll", "init", "--starting-balance", "500", "--file", str(path)])
    # Original bankroll is untouched
    assert Bankroll.load(path).starting_balance == 1000


def test_init_force_overwrites(tmp_path):
    path = tmp_path / "bankroll.json"
    Bankroll(1000).save(path)
    main(["bankroll", "init", "--starting-balance", "500", "--force", "--file", str(path)])
    assert Bankroll.load(path).starting_balance == 500


def test_bet_and_list_and_stats(tmp_path, capsys):
    path = tmp_path / "bankroll.json"
    main(["bankroll", "init", "--starting-balance", "1000", "--file", str(path)])
    capsys.readouterr()  # discard init output

    main(
        [
            "bankroll",
            "bet",
            "--description",
            "Lakers ML",
            "--stake",
            "100",
            "--decimal-odds",
            "2.0",
            "--file",
            str(path),
        ]
    )
    bet_out = capsys.readouterr().out
    assert "Lakers ML" in bet_out
    assert "#0" in bet_out

    main(["bankroll", "list", "--file", str(path)])
    list_out = capsys.readouterr().out
    assert "Lakers ML" in list_out
    assert "pending" in list_out

    main(["bankroll", "stats", "--file", str(path)])
    stats_out = capsys.readouterr().out
    assert "Starting balance: 1000.00" in stats_out
    assert "1 pending" in stats_out


def test_settle_updates_balance(tmp_path, capsys):
    path = tmp_path / "bankroll.json"
    main(["bankroll", "init", "--starting-balance", "1000", "--file", str(path)])
    main(
        [
            "bankroll", "bet",
            "--description", "Lakers ML",
            "--stake", "100",
            "--decimal-odds", "2.0",
            "--file", str(path),
        ]
    )
    capsys.readouterr()

    main(["bankroll", "settle", "--index", "0", "--outcome", "won", "--file", str(path)])
    settle_out = capsys.readouterr().out
    assert "won" in settle_out
    assert "1100.00" in settle_out

    bankroll = Bankroll.load(path)
    assert bankroll.balance == pytest.approx(1100.0)


def test_settle_invalid_index_exits(tmp_path):
    path = tmp_path / "bankroll.json"
    main(["bankroll", "init", "--starting-balance", "1000", "--file", str(path)])
    with pytest.raises(SystemExit):
        main(["bankroll", "settle", "--index", "5", "--outcome", "won", "--file", str(path)])


def test_commands_without_existing_bankroll_exit(tmp_path):
    path = tmp_path / "missing.json"
    for args in (
        ["bankroll", "list", "--file", str(path)],
        ["bankroll", "stats", "--file", str(path)],
        ["bankroll", "bet", "--description", "x", "--stake", "1", "--decimal-odds", "2.0", "--file", str(path)],
    ):
        with pytest.raises(SystemExit):
            main(args)


def test_list_with_no_bets(tmp_path, capsys):
    path = tmp_path / "bankroll.json"
    main(["bankroll", "init", "--starting-balance", "1000", "--file", str(path)])
    capsys.readouterr()
    main(["bankroll", "list", "--file", str(path)])
    assert "No bets recorded yet." in capsys.readouterr().out
