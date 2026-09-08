import pytest

from sports_betting.bankroll import Bankroll, BetOutcome


def test_place_bet_reduces_available_but_not_balance_until_settled():
    br = Bankroll(1000)
    bet = br.place_bet("Team A ML", stake=100, decimal_odds=2.0)
    assert bet.outcome == BetOutcome.PENDING
    assert br.balance == 1000  # unsettled bets don't change balance
    assert br.total_staked == 100


def test_settle_bet_won_increases_balance():
    br = Bankroll(1000)
    bet = br.place_bet("Team A ML", stake=100, decimal_odds=2.0)
    br.settle_bet(bet, BetOutcome.WON)
    assert bet.profit == pytest.approx(100.0)
    assert br.balance == pytest.approx(1100.0)


def test_settle_bet_lost_decreases_balance():
    br = Bankroll(1000)
    bet = br.place_bet("Team A ML", stake=100, decimal_odds=2.0)
    br.settle_bet(bet, BetOutcome.LOST)
    assert bet.profit == pytest.approx(-100.0)
    assert br.balance == pytest.approx(900.0)


def test_settle_bet_push_no_change():
    br = Bankroll(1000)
    bet = br.place_bet("Team A ML", stake=100, decimal_odds=2.0)
    br.settle_bet(bet, BetOutcome.PUSH)
    assert bet.profit == 0.0
    assert br.balance == pytest.approx(1000.0)


def test_cannot_stake_more_than_balance():
    br = Bankroll(100)
    with pytest.raises(ValueError):
        br.place_bet("Too big", stake=200, decimal_odds=2.0)


def test_cannot_double_settle():
    br = Bankroll(1000)
    bet = br.place_bet("Team A ML", stake=100, decimal_odds=2.0)
    br.settle_bet(bet, BetOutcome.WON)
    with pytest.raises(ValueError):
        br.settle_bet(bet, BetOutcome.LOST)


def test_roi_across_settled_bets():
    br = Bankroll(1000)
    b1 = br.place_bet("Bet 1", stake=100, decimal_odds=2.0)
    b2 = br.place_bet("Bet 2", stake=100, decimal_odds=2.0)
    br.settle_bet(b1, BetOutcome.WON)
    br.settle_bet(b2, BetOutcome.LOST)
    # profit: +100 - 100 = 0, staked: 200 -> roi 0
    assert br.roi == pytest.approx(0.0)


def test_pending_bets_list():
    br = Bankroll(1000)
    b1 = br.place_bet("Bet 1", stake=100, decimal_odds=2.0)
    br.place_bet("Bet 2", stake=100, decimal_odds=2.0)
    br.settle_bet(b1, BetOutcome.WON)
    assert len(br.pending_bets) == 1


def test_invalid_bet_construction():
    br = Bankroll(1000)
    with pytest.raises(ValueError):
        br.place_bet("Bad odds", stake=10, decimal_odds=1.0)
    with pytest.raises(ValueError):
        br.place_bet("Bad stake", stake=0, decimal_odds=2.0)


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "bankroll.json"
    br = Bankroll(1000)
    won = br.place_bet("Bet 1", stake=100, decimal_odds=2.0)
    br.place_bet("Bet 2", stake=50, decimal_odds=1.5)
    br.settle_bet(won, BetOutcome.WON)
    br.save(path)

    loaded = Bankroll.load(path)
    assert loaded.starting_balance == br.starting_balance
    assert len(loaded.bets) == 2
    assert loaded.balance == pytest.approx(br.balance)
    assert loaded.bets[0].outcome == BetOutcome.WON
    assert loaded.bets[1].outcome == BetOutcome.PENDING


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        Bankroll.load(tmp_path / "does_not_exist.json")


def test_save_creates_parent_directories(tmp_path):
    path = tmp_path / "nested" / "dir" / "bankroll.json"
    Bankroll(500).save(path)
    assert path.exists()


def test_export_csv_contents(tmp_path):
    import csv as csv_module

    br = Bankroll(1000)
    won = br.place_bet("Bet 1", stake=100, decimal_odds=2.0)
    lost = br.place_bet("Bet 2", stake=50, decimal_odds=1.5)
    br.place_bet("Bet 3", stake=20, decimal_odds=3.0)  # left pending
    br.settle_bet(won, BetOutcome.WON)
    br.settle_bet(lost, BetOutcome.LOST)

    csv_path = tmp_path / "history.csv"
    br.export_csv(csv_path)

    with csv_path.open(newline="") as f:
        rows = list(csv_module.DictReader(f))

    assert len(rows) == 3
    assert rows[0]["description"] == "Bet 1"
    assert rows[0]["outcome"] == "won"
    assert float(rows[0]["profit"]) == pytest.approx(100.0)
    assert rows[1]["outcome"] == "lost"
    assert float(rows[1]["profit"]) == pytest.approx(-50.0)
    assert rows[2]["outcome"] == "pending"
    assert float(rows[2]["profit"]) == pytest.approx(0.0)


def test_export_csv_creates_parent_directories(tmp_path):
    br = Bankroll(1000)
    br.place_bet("Bet 1", stake=10, decimal_odds=2.0)
    path = tmp_path / "nested" / "history.csv"
    br.export_csv(path)
    assert path.exists()


def test_leaderboard_ranks_by_profit_descending():
    br = Bankroll(1000)
    small_win = br.place_bet("Small win", stake=10, decimal_odds=2.0)   # +10
    big_win = br.place_bet("Big win", stake=100, decimal_odds=2.0)      # +100
    a_loss = br.place_bet("A loss", stake=50, decimal_odds=2.0)         # -50
    br.settle_bet(small_win, BetOutcome.WON)
    br.settle_bet(big_win, BetOutcome.WON)
    br.settle_bet(a_loss, BetOutcome.LOST)

    ranked = br.leaderboard(by="profit")
    descriptions = [bet.description for _, bet in ranked]
    assert descriptions == ["Big win", "Small win", "A loss"]


def test_leaderboard_excludes_pending():
    br = Bankroll(1000)
    won = br.place_bet("Won", stake=10, decimal_odds=2.0)
    br.place_bet("Still pending", stake=10, decimal_odds=2.0)
    br.settle_bet(won, BetOutcome.WON)

    ranked = br.leaderboard()
    assert len(ranked) == 1
    assert ranked[0][1].description == "Won"


def test_leaderboard_by_roi_reorders_relative_to_profit():
    br = Bankroll(1000)
    # Big absolute profit but modest ROI
    big_stake = br.place_bet("Big stake", stake=1000, decimal_odds=1.2)   # +200, 20% ROI
    # Small absolute profit but huge ROI
    small_stake = br.place_bet("Small stake", stake=10, decimal_odds=10.0)  # +90, 900% ROI
    br.settle_bet(big_stake, BetOutcome.WON)
    br.settle_bet(small_stake, BetOutcome.WON)

    by_profit = [bet.description for _, bet in br.leaderboard(by="profit")]
    by_roi = [bet.description for _, bet in br.leaderboard(by="roi")]
    assert by_profit == ["Big stake", "Small stake"]
    assert by_roi == ["Small stake", "Big stake"]


def test_leaderboard_top_limits_results():
    br = Bankroll(1000)
    for i in range(5):
        bet = br.place_bet(f"Bet {i}", stake=10, decimal_odds=2.0)
        br.settle_bet(bet, BetOutcome.WON)
    assert len(br.leaderboard(top=2)) == 2


def test_leaderboard_invalid_by_raises():
    br = Bankroll(1000)
    with pytest.raises(ValueError):
        br.leaderboard(by="nonsense")
