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

# Leaderboard: rank your settled bets best-to-worst by profit or ROI
for index, bet in bank.leaderboard(by="roi", top=5):
    print(f"#{index} {bet.description}: {bet.profit:+.2f} ({bet.profit / bet.stake:+.1%})")

# Export the full bet history to CSV
bank.export_csv("history.csv")
```

### Live odds

Fetch real-time odds from [The Odds API](https://the-odds-api.com/) (free
tier available) and feed them straight into the tools above:

```python
from sports_betting import OddsAPIClient, scan_for_arbitrage

# Reads the key from the ODDS_API_KEY env var, or pass api_key=... explicitly
client = OddsAPIClient()

games = client.get_odds("basketball_nba", regions="us", markets="h2h")
for game in games:
    print(game.home_team, "vs", game.away_team, game.best_odds_by_outcome())

# Automatically check every game for a cross-bookmaker arbitrage opportunity
for game, result in scan_for_arbitrage(games):
    print(f"{game.away_team} @ {game.home_team}: {result.profit_margin:.2%} guaranteed return")
```

## CLI usage

```bash
sports-betting convert --american +150
sports-betting convert --decimal 2.5

sports-betting ev --probability 0.55 --decimal-odds 2.0 --stake 100

sports-betting kelly --probability 0.55 --decimal-odds 2.0 --bankroll 1000 --fraction 0.5

sports-betting arbitrage --decimal-odds 2.1 2.05 --total-stake 1000

# Requires an API key: export ODDS_API_KEY=... (or pass --api-key)
sports-betting live-odds --sport basketball_nba --regions us --markets h2h
sports-betting live-arbitrage --sport soccer_epl --regions uk

# Bankroll tracking (persisted to ~/.sports_betting/bankroll.json by default)
sports-betting bankroll init --starting-balance 1000
sports-betting bankroll bet --description "Lakers ML" --stake 50 --decimal-odds 1.91
sports-betting bankroll settle --index 0 --outcome won
sports-betting bankroll list
sports-betting bankroll stats
sports-betting bankroll leaderboard --by roi --top 5
sports-betting bankroll export --output history.csv
```

## CLI commands

| Command                     | Purpose                                                    |
|------------------------------|-------------------------------------------------------------|
| `convert`                   | Convert odds between American, decimal, and implied probability |
| `ev`                        | Calculate the expected value of a bet                      |
| `kelly`                     | Calculate a Kelly criterion stake                           |
| `arbitrage`                 | Check a set of odds for a cross-bookmaker arbitrage opportunity |
| `live-odds`                 | Fetch live odds for a sport from The Odds API (needs `ODDS_API_KEY`) |
| `live-arbitrage`            | Scan live odds for a sport for arbitrage opportunities      |
| `bankroll init`             | Create a new persistent bankroll                            |
| `bankroll bet`              | Place a bet against the bankroll                            |
| `bankroll settle`           | Mark a pending bet won, lost, or push                       |
| `bankroll list`             | List every recorded bet                                     |
| `bankroll stats`            | Show balance, net profit, ROI, and bet counts               |
| `bankroll leaderboard`      | Rank settled bets best-to-worst by profit or ROI            |
| `bankroll export`           | Export the full bet history to a CSV file                   |

## Module overview

| Module           | Purpose                                                    |
|------------------|-------------------------------------------------------------|
| `odds.py`        | Convert between American, decimal, fractional odds, and implied probability; remove the vig from a market to get fair probabilities |
| `ev.py`          | Expected value of a bet given your own probability estimate |
| `kelly.py`       | Kelly criterion stake sizing (with fractional Kelly support) |
| `arbitrage.py`   | Detect arbitrage across bookmakers and compute equal-payout stakes |
| `bankroll.py`    | Track a bankroll's bet history, balance, and ROI            |
| `live_odds.py`   | Fetch live odds from The Odds API and check them for arbitrage |
| `cli.py`         | Command-line interface tying the above together             |

## Development

```bash
pip install -e ".[dev]"
pytest
```
