import pytest

from sports_betting.kelly import kelly_fraction, kelly_stake


def test_kelly_fraction_known_value():
    # p=0.6, decimal odds=2.0 -> b=1 -> f* = (1*0.6 - 0.4)/1 = 0.2
    assert kelly_fraction(0.6, 2.0) == pytest.approx(0.2)


def test_kelly_fraction_no_edge_clamped_to_zero():
    assert kelly_fraction(0.4, 2.0) == 0.0


def test_kelly_fraction_fair_odds_is_zero():
    assert kelly_fraction(0.5, 2.0) == pytest.approx(0.0, abs=1e-9)


def test_kelly_stake_scales_with_bankroll_and_fraction():
    stake_full = kelly_stake(0.6, 2.0, bankroll=1000, fraction=1.0)
    stake_half = kelly_stake(0.6, 2.0, bankroll=1000, fraction=0.5)
    assert stake_full == pytest.approx(200.0)
    assert stake_half == pytest.approx(100.0)


def test_kelly_stake_invalid_bankroll():
    with pytest.raises(ValueError):
        kelly_stake(0.6, 2.0, bankroll=-1)


def test_kelly_fraction_invalid_probability():
    with pytest.raises(ValueError):
        kelly_fraction(1.5, 2.0)
