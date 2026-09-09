"""Compare a player prop line to that player's history against the same opponent.

This module intentionally doesn't fetch player stats or props itself - there's
no live feed for either wired into this project (The Odds API's player-prop
markets need a paid plan and per-event calls, and there's no play-by-play
stats source configured at all). Instead, it works on game logs and prop
lines you supply as simple CSVs, so it's ready to plug into whichever data
source you actually have (a manual spreadsheet, a paid odds/stats API, a
weekly copy-paste) without committing to one now.

CSV formats
-----------
Game log (one row per game a player has played)::

    player,team,opponent,date,stat_type,stat_value
    Josh Allen,BUF,MIA,2025-09-10,passing_yards,278

Props (one row per current prop you want checked)::

    player,team,opponent,stat_type,line
    Josh Allen,BUF,MIA,passing_yards,245.5
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class PropResult(str, Enum):
    OVER = "over"
    UNDER = "under"
    PUSH = "push"


@dataclass(frozen=True)
class PlayerGameLog:
    """A single stat line from a game a player actually played."""

    player: str
    team: str
    opponent: str
    date: str  # ISO date, e.g. "2025-09-10"
    stat_type: str  # e.g. "points", "passing_yards", "rebounds"
    stat_value: float


@dataclass(frozen=True)
class PlayerProp:
    """A current prop line to check against history."""

    player: str
    team: str
    opponent: str
    stat_type: str
    line: float


@dataclass(frozen=True)
class PropHistoryResult:
    """How a player has fared, in past games against this same opponent,
    relative to their current prop line for the same stat.
    """

    prop: PlayerProp
    games: list[PlayerGameLog]  # matching games, most recent last

    @property
    def games_played(self) -> int:
        return len(self.games)

    @property
    def overs(self) -> int:
        return sum(1 for g in self.games if result_for_game(g, self.prop.line) == PropResult.OVER)

    @property
    def unders(self) -> int:
        return sum(1 for g in self.games if result_for_game(g, self.prop.line) == PropResult.UNDER)

    @property
    def pushes(self) -> int:
        return sum(1 for g in self.games if result_for_game(g, self.prop.line) == PropResult.PUSH)

    @property
    def hit_rate_over(self) -> float | None:
        """Fraction of matching games that cleared the line. None with no history."""
        if not self.games:
            return None
        return self.overs / self.games_played

    @property
    def average_stat(self) -> float | None:
        if not self.games:
            return None
        return sum(g.stat_value for g in self.games) / self.games_played


def result_for_game(game: PlayerGameLog, line: float) -> PropResult:
    """Whether a single game's stat would have gone over, under, or pushed a line."""
    if game.stat_value > line:
        return PropResult.OVER
    if game.stat_value < line:
        return PropResult.UNDER
    return PropResult.PUSH


def history_vs_opponent(
    prop: PlayerProp, game_logs: list[PlayerGameLog]
) -> PropHistoryResult:
    """Filter a player's full game log down to games against this prop's
    opponent (and matching stat type), then check each one against the
    current line.
    """
    matching = [
        g
        for g in game_logs
        if g.player == prop.player
        and g.opponent == prop.opponent
        and g.stat_type == prop.stat_type
    ]
    return PropHistoryResult(prop=prop, games=matching)


def compare_props(
    props: list[PlayerProp], game_logs: list[PlayerGameLog], team: str | None = None
) -> list[PropHistoryResult]:
    """Run every prop through ``history_vs_opponent``, optionally filtered
    down to props for players on a single ``team``.
    """
    selected = [p for p in props if team is None or p.team == team] if team else props
    return [history_vs_opponent(p, game_logs) for p in selected]


def load_game_logs_csv(path: Path) -> list[PlayerGameLog]:
    with Path(path).open(newline="") as f:
        return [
            PlayerGameLog(
                player=row["player"],
                team=row["team"],
                opponent=row["opponent"],
                date=row["date"],
                stat_type=row["stat_type"],
                stat_value=float(row["stat_value"]),
            )
            for row in csv.DictReader(f)
        ]


def load_props_csv(path: Path) -> list[PlayerProp]:
    with Path(path).open(newline="") as f:
        return [
            PlayerProp(
                player=row["player"],
                team=row["team"],
                opponent=row["opponent"],
                stat_type=row["stat_type"],
                line=float(row["line"]),
            )
            for row in csv.DictReader(f)
        ]


GAME_LOG_FIELDNAMES = ["player", "team", "opponent", "date", "stat_type", "stat_value"]
PROP_FIELDNAMES = ["player", "team", "opponent", "stat_type", "line"]


def save_game_logs_csv(path: Path, game_logs: list[PlayerGameLog]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=GAME_LOG_FIELDNAMES)
        writer.writeheader()
        for log in game_logs:
            writer.writerow(
                {
                    "player": log.player,
                    "team": log.team,
                    "opponent": log.opponent,
                    "date": log.date,
                    "stat_type": log.stat_type,
                    "stat_value": log.stat_value,
                }
            )


def save_props_csv(path: Path, props: list[PlayerProp]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PROP_FIELDNAMES)
        writer.writeheader()
        for prop in props:
            writer.writerow(
                {
                    "player": prop.player,
                    "team": prop.team,
                    "opponent": prop.opponent,
                    "stat_type": prop.stat_type,
                    "line": prop.line,
                }
            )


def _load_game_logs_if_exists(path: Path) -> list[PlayerGameLog]:
    return load_game_logs_csv(path) if Path(path).exists() else []


def _load_props_if_exists(path: Path) -> list[PlayerProp]:
    return load_props_csv(path) if Path(path).exists() else []


def append_game_log(path: Path, log: PlayerGameLog) -> None:
    """Add one played game to a game-log CSV, creating the file (with header)
    if it doesn't exist yet. This is the weekly step that turns last week's
    prop into history: once a game is final, record what actually happened.
    """
    game_logs = _load_game_logs_if_exists(path)
    game_logs.append(log)
    save_game_logs_csv(path, game_logs)


def upsert_prop(path: Path, prop: PlayerProp) -> bool:
    """Add or update this week's line for a player+opponent+stat in a props
    CSV, creating the file if it doesn't exist. If a prop already exists for
    the same (player, team, opponent, stat_type), its line is replaced
    in place rather than duplicated; otherwise the new prop is appended.

    Returns True if an existing row was replaced, False if one was added.
    """
    props = _load_props_if_exists(path)
    key = (prop.player, prop.team, prop.opponent, prop.stat_type)
    for i, existing in enumerate(props):
        if (existing.player, existing.team, existing.opponent, existing.stat_type) == key:
            props[i] = prop
            save_props_csv(path, props)
            return True
    props.append(prop)
    save_props_csv(path, props)
    return False


def remove_prop(path: Path, player: str, team: str, opponent: str, stat_type: str) -> bool:
    """Remove a single prop (e.g. a matchup that's no longer this week's
    slate) from a props CSV. Returns True if a row was removed.
    """
    props = _load_props_if_exists(path)
    key = (player, team, opponent, stat_type)
    remaining = [
        p for p in props if (p.player, p.team, p.opponent, p.stat_type) != key
    ]
    if len(remaining) == len(props):
        return False
    save_props_csv(path, remaining)
    return True
