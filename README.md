# sports-betting

A small Python toolkit for sports betting math: odds conversions, expected
value, Kelly criterion staking, arbitrage detection, and bankroll tracking.

This is an analysis/education tool, not a betting bot — it doesn't place
bets or pull live odds. It's meant to help you reason about prices you
already have in front of you.

## Install

```bash
pip install -e ".[dev]"
```

## Library usage

```python
from sports_betting import (
    american_to_decimal,
    decimal_to_implied_probability,
    expected_value,
    kelly_stake,
    find_arbitrage,
    Bankroll,
    BetOutcome,
)

# Odds conversion
decimal_odds = american_to_decimal(150)          # +150 -> 2.5
implied = decimal_to_implied_probability(decimal_odds)  # 0.40 (40%)

# Expected value: is a bet worth making given YOUR probability estimate?
ev = expected_value(probability=0.45, decimal_odds=2.5, stake=10)

# Kelly criterion: how much of your bankroll to stake
stake = kelly_stake(probability=0.45, decimal_odds=2.5, bankroll=1000, fraction=0.5)

# Arbitrage: check odds from two different books for a guaranteed profit
result = find_arbitrage([2.10, 2.05])
if result.is_arbitrage:
    print(f"Guaranteed return: {result.profit_margin:.2%}")

# Bankroll tracking
bank = Bankroll(starting_balance=1000)
bet = bank.place_bet("Lakers ML", stake=50, decimal_odds=1.91)
bank.settle_bet(bet, BetOutcome.WON)
print(bank.balance, bank.roi)
```

## CLI usage

```bash
sports-betting convert --american +150
sports-betting convert --decimal 2.5

sports-betting ev --probability 0.55 --decimal-odds 2.0 --stake 100

sports-betting kelly --probability 0.55 --decimal-odds 2.0 --bankroll 1000 --fraction 0.5

sports-betting arbitrage --decimal-odds 2.1 2.05 --total-stake 1000
```

## Module overview

| Module           | Purpose                                                    |
|------------------|-------------------------------------------------------------|
| `odds.py`        | Convert between American, decimal, fractional odds, and implied probability; remove the vig from a market to get fair probabilities |
| `ev.py`          | Expected value of a bet given your own probability estimate |
| `kelly.py`       | Kelly criterion stake sizing (with fractional Kelly support) |
| `arbitrage.py`   | Detect arbitrage across bookmakers and compute equal-payout stakes |
| `bankroll.py`    | Track a bankroll's bet history, balance, and ROI            |
| `cli.py`         | Command-line interface tying the above together             |

## Development

```bash
pip install -e ".[dev]"
pytest
```
