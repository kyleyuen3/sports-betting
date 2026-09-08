"""Simple bankroll and bet-history tracking."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

DEFAULT_BANKROLL_PATH = Path.home() / ".sports_betting" / "bankroll.json"


class BetOutcome(str, Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    PUSH = "push"  # stake returned, no profit or loss


@dataclass
class Bet:
    description: str
    stake: float
    decimal_odds: float
    outcome: BetOutcome = BetOutcome.PENDING
    placed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.stake <= 0:
            raise ValueError("stake must be positive")
        if self.decimal_odds <= 1:
            raise ValueError("decimal_odds must be greater than 1")

    @property
    def profit(self) -> float:
        """Net profit (or loss, as a negative number) once settled."""
        if self.outcome == BetOutcome.WON:
            return self.stake * (self.decimal_odds - 1)
        if self.outcome == BetOutcome.LOST:
            return -self.stake
        return 0.0  # pending or push


class Bankroll:
    """Tracks a starting balance plus a ledger of placed and settled bets."""

    def __init__(self, starting_balance: float):
        if starting_balance < 0:
            raise ValueError("starting_balance must be non-negative")
        self.starting_balance = starting_balance
        self.bets: list[Bet] = []

    def place_bet(self, description: str, stake: float, decimal_odds: float) -> Bet:
        if stake > self.balance:
            raise ValueError(
                f"stake {stake} exceeds current balance {self.balance}"
            )
        bet = Bet(description=description, stake=stake, decimal_odds=decimal_odds)
        self.bets.append(bet)
        return bet

    def settle_bet(self, bet: Bet, outcome: BetOutcome) -> None:
        if bet not in self.bets:
            raise ValueError("bet does not belong to this bankroll")
        if bet.outcome != BetOutcome.PENDING:
            raise ValueError("bet has already been settled")
        bet.outcome = outcome

    @property
    def balance(self) -> float:
        return self.starting_balance + sum(bet.profit for bet in self.bets)

    @property
    def total_staked(self) -> float:
        return sum(bet.stake for bet in self.bets)

    @property
    def pending_bets(self) -> list[Bet]:
        return [b for b in self.bets if b.outcome == BetOutcome.PENDING]

    @property
    def roi(self) -> float:
        """Return on investment across all settled bets, as a fraction."""
        settled = [b for b in self.bets if b.outcome != BetOutcome.PENDING]
        staked = sum(b.stake for b in settled)
        if staked == 0:
            return 0.0
        return sum(b.profit for b in settled) / staked

    def to_dict(self) -> dict:
        return {
            "starting_balance": self.starting_balance,
            "bets": [
                {
                    "description": bet.description,
                    "stake": bet.stake,
                    "decimal_odds": bet.decimal_odds,
                    "outcome": bet.outcome.value,
                    "placed_at": bet.placed_at.isoformat(),
                }
                for bet in self.bets
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Bankroll":
        bankroll = cls(starting_balance=data["starting_balance"])
        bankroll.bets = [
            Bet(
                description=b["description"],
                stake=b["stake"],
                decimal_odds=b["decimal_odds"],
                outcome=BetOutcome(b["outcome"]),
                placed_at=datetime.fromisoformat(b["placed_at"]),
            )
            for b in data["bets"]
        ]
        return bankroll

    def save(self, path: Path = DEFAULT_BANKROLL_PATH) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path = DEFAULT_BANKROLL_PATH) -> "Bankroll":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"No bankroll found at {path}. "
                "Run 'sports-betting bankroll init' first."
            )
        return cls.from_dict(json.loads(path.read_text()))
