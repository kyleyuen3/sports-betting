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
