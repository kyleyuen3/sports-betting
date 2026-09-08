import pytest

from sports_betting.arbitrage import arbitrage_stakes, find_arbitrage


def test_find_arbitrage_true():
    # 1/2.1 + 1/2.05 = 0.4762 + 0.4878 = 0.964 < 1 -> arbitrage
    result = find_arbitrage([2.1, 2.05])
    assert result.is_arbitrage is True
    assert result.total_implied_probability < 1.0
    assert result.profit_margin > 0


def test_find_arbitrage_false():
    result = find_arbitrage([1.8, 1.8])
    assert result.is_arbitrage is False
    assert result.profit_margin == 0.0


def test_find_arbitrage_empty_raises():
    with pytest.raises(ValueError):
        find_arbitrage([])


def test_arbitrage_stakes_equal_payout():
    odds = [2.1, 2.05]
    total_stake = 1000
    stakes = arbitrage_stakes(odds, total_stake)
    assert sum(stakes) == pytest.approx(total_stake)

    payouts = [stake * o for stake, o in zip(stakes, odds)]
    assert payouts[0] == pytest.approx(payouts[1])
    # Payout should exceed total stake since this is a real arbitrage
    assert payouts[0] > total_stake


def test_arbitrage_stakes_invalid_total_stake():
    with pytest.raises(ValueError):
        arbitrage_stakes([2.0, 2.0], 0)
