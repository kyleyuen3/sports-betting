import math

import pytest

from sports_betting.odds import (
    american_to_decimal,
    decimal_to_american,
    decimal_to_fractional,
    decimal_to_implied_probability,
    fractional_to_decimal,
    implied_probability_to_decimal,
    remove_vig,
)


def test_american_to_decimal_positive():
    assert american_to_decimal(150) == pytest.approx(2.5)


def test_american_to_decimal_negative():
    assert american_to_decimal(-200) == pytest.approx(1.5)


def test_american_to_decimal_zero_raises():
    with pytest.raises(ValueError):
        american_to_decimal(0)


def test_decimal_to_american_favorite_and_underdog():
    assert decimal_to_american(2.5) == pytest.approx(150)
    assert decimal_to_american(1.5) == pytest.approx(-200)


def test_decimal_to_american_invalid():
    with pytest.raises(ValueError):
        decimal_to_american(1.0)


def test_round_trip_american_decimal():
    for american in [110, 250, -110, -350, 100]:
        decimal = american_to_decimal(american)
        assert decimal_to_american(decimal) == pytest.approx(american, abs=1e-6)


def test_fractional_to_decimal():
    assert fractional_to_decimal("3/2") == pytest.approx(2.5)
    assert fractional_to_decimal("1/1") == pytest.approx(2.0)


def test_fractional_to_decimal_invalid():
    with pytest.raises(ValueError):
        fractional_to_decimal("-1/2")


def test_decimal_to_fractional():
    assert decimal_to_fractional(2.5) == "3/2"


def test_implied_probability_round_trip():
    decimal = 2.5
    p = decimal_to_implied_probability(decimal)
    assert p == pytest.approx(0.4)
    assert implied_probability_to_decimal(p) == pytest.approx(decimal)


def test_implied_probability_invalid():
    with pytest.raises(ValueError):
        decimal_to_implied_probability(1.0)
    with pytest.raises(ValueError):
        implied_probability_to_decimal(0)
    with pytest.raises(ValueError):
        implied_probability_to_decimal(1.5)


def test_remove_vig_sums_to_one():
    # Two-way market with juice: implied probs sum to > 1
    odds = [1.91, 1.91]
    fair = remove_vig(odds)
    assert math.isclose(sum(fair), 1.0, rel_tol=1e-9)
    assert fair[0] == pytest.approx(fair[1])


def test_remove_vig_three_way():
    odds = [2.5, 3.2, 3.0]
    fair = remove_vig(odds)
    assert math.isclose(sum(fair), 1.0, rel_tol=1e-9)
    assert all(0 < p < 1 for p in fair)


def test_remove_vig_empty_raises():
    with pytest.raises(ValueError):
        remove_vig([])
