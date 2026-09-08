import pytest

from sports_betting.ev import ev_percentage, expected_value, is_positive_ev


def test_expected_value_positive_edge():
    # 60% true win probability at even money (decimal 2.0) is +EV
    ev = expected_value(0.6, 2.0, stake=10)
    assert ev == pytest.approx(2.0)


def test_expected_value_negative_edge():
    ev = expected_value(0.4, 2.0, stake=10)
    assert ev == pytest.approx(-2.0)


def test_expected_value_fair_odds_is_zero():
    ev = expected_value(0.5, 2.0, stake=100)
    assert ev == pytest.approx(0.0)


def test_is_positive_ev():
    assert is_positive_ev(0.6, 2.0) is True
    assert is_positive_ev(0.4, 2.0) is False


def test_ev_percentage():
    assert ev_percentage(0.6, 2.0) == pytest.approx(20.0)


def test_expected_value_invalid_inputs():
    with pytest.raises(ValueError):
        expected_value(1.5, 2.0)
    with pytest.raises(ValueError):
        expected_value(0.5, 1.0)
    with pytest.raises(ValueError):
        expected_value(0.5, 2.0, stake=-1)
