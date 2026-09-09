"""Command-line interface for the sports-betting toolkit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .arbitrage import find_arbitrage, arbitrage_stakes
from .bankroll import Bankroll, BetOutcome, DEFAULT_BANKROLL_PATH
from .ev import expected_value
from .kelly import kelly_fraction, kelly_stake
from .live_odds import OddsAPIClient, OddsAPIError, scan_for_arbitrage
from .player_props import (
    PlayerGameLog,
    PlayerProp,
    append_game_log,
    compare_props,
    load_game_logs_csv,
    load_props_csv,
    remove_prop,
    upsert_prop,
)
from .odds import (
    american_to_decimal,
    decimal_to_american,
    decimal_to_implied_probability,
)


def _cmd_convert(args: argparse.Namespace) -> None:
    if args.american is not None:
        decimal = american_to_decimal(args.american)
    else:
        decimal = args.decimal

    american = decimal_to_american(decimal)
    implied = decimal_to_implied_probability(decimal)
    print(f"Decimal odds:       {decimal:.4f}")
    print(f"American odds:      {american:+.0f}")
    print(f"Implied probability: {implied * 100:.2f}%")


def _cmd_ev(args: argparse.Namespace) -> None:
    ev = expected_value(args.probability, args.decimal_odds, args.stake)
    print(f"Expected value: {ev:+.4f}")
    print("Positive EV" if ev > 0 else "Negative or zero EV")


def _cmd_kelly(args: argparse.Namespace) -> None:
    f = kelly_fraction(args.probability, args.decimal_odds)
    print(f"Kelly fraction: {f * 100:.2f}% of bankroll")
    if args.bankroll is not None:
        stake = kelly_stake(args.probability, args.decimal_odds, args.bankroll, args.fraction)
        print(f"Recommended stake ({args.fraction:g}x Kelly): {stake:.2f}")


def _cmd_arbitrage(args: argparse.Namespace) -> None:
    result = find_arbitrage(args.decimal_odds)
    print(f"Total implied probability: {result.total_implied_probability * 100:.2f}%")
    if result.is_arbitrage:
        print(f"Arbitrage found! Guaranteed return: {result.profit_margin * 100:.2f}%")
        if args.total_stake is not None:
            stakes = arbitrage_stakes(args.decimal_odds, args.total_stake)
            for i, (odds, stake) in enumerate(zip(args.decimal_odds, stakes), start=1):
                print(f"  Outcome {i} (odds {odds:g}): stake {stake:.2f}")
    else:
        print("No arbitrage opportunity.")


def _cmd_live_odds(args: argparse.Namespace) -> None:
    try:
        client = OddsAPIClient(api_key=args.api_key)
        games = client.get_odds(args.sport, regions=args.regions, markets=args.markets)
    except (ValueError, OddsAPIError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if not games:
        print("No upcoming games found.")
        return

    for game in games:
        print(f"{game.away_team} @ {game.home_team}  ({game.commence_time})")
        for outcome_name, (price, bookmaker) in game.best_odds_by_outcome().items():
            print(f"  {outcome_name}: {price:g} (best at {bookmaker})")


def _cmd_live_arbitrage(args: argparse.Namespace) -> None:
    try:
        client = OddsAPIClient(api_key=args.api_key)
        games = client.get_odds(args.sport, regions=args.regions, markets=args.markets)
    except (ValueError, OddsAPIError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    opportunities = scan_for_arbitrage(games)
    if not opportunities:
        print("No arbitrage opportunities found.")
        return

    for game, result in opportunities:
        print(
            f"{game.away_team} @ {game.home_team}: "
            f"{result.profit_margin * 100:.2f}% guaranteed return"
        )
        for outcome_name, (price, bookmaker) in game.best_odds_by_outcome().items():
            print(f"  {outcome_name}: {price:g} at {bookmaker}")


def _load_bankroll_or_exit(path: Path) -> Bankroll:
    try:
        return Bankroll.load(path)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


def _cmd_bankroll_init(args: argparse.Namespace) -> None:
    path = Path(args.file)
    if path.exists() and not args.force:
        print(f"Error: a bankroll already exists at {path} (use --force to overwrite)", file=sys.stderr)
        raise SystemExit(1)
    bankroll = Bankroll(starting_balance=args.starting_balance)
    bankroll.save(path)
    print(f"Created bankroll with starting balance {args.starting_balance:.2f} at {path}")


def _cmd_bankroll_bet(args: argparse.Namespace) -> None:
    path = Path(args.file)
    bankroll = _load_bankroll_or_exit(path)
    try:
        bet = bankroll.place_bet(args.description, args.stake, args.decimal_odds)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    bankroll.save(path)
    index = len(bankroll.bets) - 1
    print(f"Placed bet #{index}: \"{bet.description}\" — stake {bet.stake:.2f} @ {bet.decimal_odds:g}")
    print(f"Balance: {bankroll.balance:.2f}")


def _cmd_bankroll_settle(args: argparse.Namespace) -> None:
    path = Path(args.file)
    bankroll = _load_bankroll_or_exit(path)
    if not 0 <= args.index < len(bankroll.bets):
        print(f"Error: no bet at index {args.index} (0-{len(bankroll.bets) - 1})", file=sys.stderr)
        raise SystemExit(1)
    bet = bankroll.bets[args.index]
    try:
        bankroll.settle_bet(bet, BetOutcome(args.outcome))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    bankroll.save(path)
    print(f"Settled bet #{args.index} \"{bet.description}\" as {bet.outcome.value}: profit {bet.profit:+.2f}")
    print(f"Balance: {bankroll.balance:.2f}")


def _cmd_bankroll_list(args: argparse.Namespace) -> None:
    bankroll = _load_bankroll_or_exit(Path(args.file))
    if not bankroll.bets:
        print("No bets recorded yet.")
        return

    for i, bet in enumerate(bankroll.bets):
        profit_str = f"{bet.profit:+.2f}" if bet.outcome != BetOutcome.PENDING else "pending"
        placed = bet.placed_at.strftime("%Y-%m-%d %H:%M")
        print(f"[{i}] {placed}  {bet.description}")
        print(
            f"     stake {bet.stake:.2f} @ {bet.decimal_odds:g}   "
            f"outcome={bet.outcome.value}   profit={profit_str}"
        )


def _cmd_bankroll_stats(args: argparse.Namespace) -> None:
    bankroll = _load_bankroll_or_exit(Path(args.file))
    settled = [b for b in bankroll.bets if b.outcome != BetOutcome.PENDING]
    wins = sum(1 for b in settled if b.outcome == BetOutcome.WON)
    losses = sum(1 for b in settled if b.outcome == BetOutcome.LOST)
    pushes = sum(1 for b in settled if b.outcome == BetOutcome.PUSH)
    net = bankroll.balance - bankroll.starting_balance

    print(f"Starting balance: {bankroll.starting_balance:.2f}")
    print(f"Current balance:  {bankroll.balance:.2f}")
    print(f"Net profit:       {net:+.2f}")
    print(f"Total staked:     {bankroll.total_staked:.2f}")
    print(f"ROI (settled):    {bankroll.roi * 100:+.2f}%")
    print(
        f"Bets: {len(bankroll.bets)} total "
        f"({len(bankroll.pending_bets)} pending, {wins} won, {losses} lost, {pushes} push)"
    )


def _cmd_bankroll_export(args: argparse.Namespace) -> None:
    bankroll = _load_bankroll_or_exit(Path(args.file))
    output_path = Path(args.output)
    bankroll.export_csv(output_path)
    print(f"Exported {len(bankroll.bets)} bet(s) to {output_path}")


def _cmd_bankroll_leaderboard(args: argparse.Namespace) -> None:
    bankroll = _load_bankroll_or_exit(Path(args.file))
    ranked = bankroll.leaderboard(by=args.by, top=args.top)
    if not ranked:
        print("No settled bets yet.")
        return

    header = f"{'#':>3}  {'Bet':>5}  {'Description':<30}{'Stake':>10}{'Odds':>8}{'Outcome':>10}{'Profit':>10}{'ROI':>9}"
    print(header)
    for rank, (index, bet) in enumerate(ranked, start=1):
        roi = bet.profit / bet.stake * 100
        description = bet.description if len(bet.description) <= 30 else bet.description[:27] + "..."
        print(
            f"{rank:>3}  {'#' + str(index):>5}  {description:<30}"
            f"{bet.stake:>10.2f}{bet.decimal_odds:>8g}{bet.outcome.value:>10}"
            f"{bet.profit:>+10.2f}{roi:>+8.1f}%"
        )


def _cmd_props_log(args: argparse.Namespace) -> None:
    log = PlayerGameLog(
        player=args.player,
        team=args.team,
        opponent=args.opponent,
        date=args.date,
        stat_type=args.stat_type,
        stat_value=args.value,
    )
    append_game_log(args.logs, log)
    print(f"Logged {log.player} vs {log.opponent} on {log.date}: {log.stat_type}={log.stat_value:g}")


def _cmd_props_set_line(args: argparse.Namespace) -> None:
    prop = PlayerProp(
        player=args.player,
        team=args.team,
        opponent=args.opponent,
        stat_type=args.stat_type,
        line=args.line,
    )
    replaced = upsert_prop(args.props, prop)
    verb = "Updated" if replaced else "Added"
    print(f"{verb} line: {prop.player} ({prop.team}) vs {prop.opponent} {prop.stat_type} {prop.line:g}")


def _cmd_props_remove_line(args: argparse.Namespace) -> None:
    removed = remove_prop(args.props, args.player, args.team, args.opponent, args.stat_type)
    if removed:
        print(f"Removed line: {args.player} ({args.team}) vs {args.opponent} {args.stat_type}")
    else:
        print("No matching prop found - nothing removed.", file=sys.stderr)
        raise SystemExit(1)


def _cmd_props_compare(args: argparse.Namespace) -> None:
    try:
        props = load_props_csv(args.props)
        game_logs = load_game_logs_csv(args.logs)
    except (FileNotFoundError, KeyError) as exc:
        print(f"Error reading CSV: {exc}", file=sys.stderr)
        raise SystemExit(1)

    results = compare_props(props, game_logs, team=args.team)
    if not results:
        print("No props matched." if args.team else "No props found.")
        return

    header = f"{'Player':<20}{'Opp':>5}  {'Stat':<16}{'Line':>8}{'Games':>7}{'O-U-P':>9}{'Hit%':>8}{'Avg':>9}"
    print(header)
    for result in results:
        prop = result.prop
        hit_rate = f"{result.hit_rate_over * 100:.0f}%" if result.hit_rate_over is not None else "n/a"
        avg = f"{result.average_stat:.1f}" if result.average_stat is not None else "n/a"
        record = f"{result.overs}-{result.unders}-{result.pushes}"
        print(
            f"{prop.player:<20}{prop.opponent:>5}  {prop.stat_type:<16}{prop.line:>8g}"
            f"{result.games_played:>7}{record:>9}{hit_rate:>8}{avg:>9}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sports-betting",
        description="Odds conversion, EV, Kelly staking, and arbitrage tools.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_convert = sub.add_parser("convert", help="Convert between odds formats")
    group = p_convert.add_mutually_exclusive_group(required=True)
    group.add_argument("--american", type=float, help="American odds, e.g. +150 or -200")
    group.add_argument("--decimal", type=float, help="Decimal odds, e.g. 2.5")
    p_convert.set_defaults(func=_cmd_convert)

    p_ev = sub.add_parser("ev", help="Calculate expected value of a bet")
    p_ev.add_argument("--probability", type=float, required=True, help="Your win probability estimate (0-1)")
    p_ev.add_argument("--decimal-odds", type=float, required=True, dest="decimal_odds")
    p_ev.add_argument("--stake", type=float, default=1.0)
    p_ev.set_defaults(func=_cmd_ev)

    p_kelly = sub.add_parser("kelly", help="Calculate Kelly criterion stake")
    p_kelly.add_argument("--probability", type=float, required=True)
    p_kelly.add_argument("--decimal-odds", type=float, required=True, dest="decimal_odds")
    p_kelly.add_argument("--bankroll", type=float, default=None)
    p_kelly.add_argument("--fraction", type=float, default=1.0, help="Kelly fraction multiplier, e.g. 0.5 for half Kelly")
    p_kelly.set_defaults(func=_cmd_kelly)

    p_arb = sub.add_parser("arbitrage", help="Check a set of odds for an arbitrage opportunity")
    p_arb.add_argument(
        "--decimal-odds",
        type=float,
        nargs="+",
        required=True,
        dest="decimal_odds",
        help="Best decimal odds for each outcome, e.g. --decimal-odds 2.1 2.05",
    )
    p_arb.add_argument("--total-stake", type=float, default=None, dest="total_stake")
    p_arb.set_defaults(func=_cmd_arbitrage)

    p_live = sub.add_parser("live-odds", help="Fetch live odds for a sport (needs an ODDS_API_KEY)")
    p_live.add_argument("--sport", required=True, help='Sport key, e.g. "basketball_nba", "soccer_epl"')
    p_live.add_argument("--regions", default="us", help='Bookmaker regions, e.g. "us", "uk", "eu"')
    p_live.add_argument("--markets", default="h2h", help='Bet types, e.g. "h2h", "spreads", "totals"')
    p_live.add_argument("--api-key", default=None, dest="api_key", help="Overrides the ODDS_API_KEY env var")
    p_live.set_defaults(func=_cmd_live_odds)

    p_live_arb = sub.add_parser("live-arbitrage", help="Scan live odds for a sport for arbitrage opportunities")
    p_live_arb.add_argument("--sport", required=True)
    p_live_arb.add_argument("--regions", default="us")
    p_live_arb.add_argument("--markets", default="h2h")
    p_live_arb.add_argument("--api-key", default=None, dest="api_key")
    p_live_arb.set_defaults(func=_cmd_live_arbitrage)

    p_bankroll = sub.add_parser("bankroll", help="Track a persistent bankroll and bet history")
    bankroll_sub = p_bankroll.add_subparsers(dest="bankroll_command", required=True)

    def add_file_arg(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--file",
            default=str(DEFAULT_BANKROLL_PATH),
            help=f"Path to the bankroll file (default: {DEFAULT_BANKROLL_PATH})",
        )

    p_bank_init = bankroll_sub.add_parser("init", help="Create a new bankroll")
    p_bank_init.add_argument("--starting-balance", type=float, required=True, dest="starting_balance")
    p_bank_init.add_argument("--force", action="store_true", help="Overwrite an existing bankroll file")
    add_file_arg(p_bank_init)
    p_bank_init.set_defaults(func=_cmd_bankroll_init)

    p_bank_bet = bankroll_sub.add_parser("bet", help="Place a new bet")
    p_bank_bet.add_argument("--description", required=True)
    p_bank_bet.add_argument("--stake", type=float, required=True)
    p_bank_bet.add_argument("--decimal-odds", type=float, required=True, dest="decimal_odds")
    add_file_arg(p_bank_bet)
    p_bank_bet.set_defaults(func=_cmd_bankroll_bet)

    p_bank_settle = bankroll_sub.add_parser("settle", help="Settle a pending bet")
    p_bank_settle.add_argument("--index", type=int, required=True, help="Bet index, from `bankroll list`")
    p_bank_settle.add_argument(
        "--outcome", required=True, choices=[o.value for o in BetOutcome if o != BetOutcome.PENDING]
    )
    add_file_arg(p_bank_settle)
    p_bank_settle.set_defaults(func=_cmd_bankroll_settle)

    p_bank_list = bankroll_sub.add_parser("list", help="List every recorded bet")
    add_file_arg(p_bank_list)
    p_bank_list.set_defaults(func=_cmd_bankroll_list)

    p_bank_stats = bankroll_sub.add_parser("stats", help="Show bankroll balance, ROI, and bet counts")
    add_file_arg(p_bank_stats)
    p_bank_stats.set_defaults(func=_cmd_bankroll_stats)

    p_bank_export = bankroll_sub.add_parser("export", help="Export the full bet history to a CSV file")
    p_bank_export.add_argument("--output", required=True, help="Path to write the CSV file to")
    add_file_arg(p_bank_export)
    p_bank_export.set_defaults(func=_cmd_bankroll_export)

    p_bank_lb = bankroll_sub.add_parser("leaderboard", help="Rank your settled bets from best to worst")
    p_bank_lb.add_argument("--by", choices=["profit", "roi"], default="profit", help="Ranking metric (default: profit)")
    p_bank_lb.add_argument("--top", type=int, default=None, help="Only show the top N bets")
    add_file_arg(p_bank_lb)
    p_bank_lb.set_defaults(func=_cmd_bankroll_leaderboard)

    p_props = sub.add_parser("props", help="Compare player props to their history against the same opponent")
    props_sub = p_props.add_subparsers(dest="props_command", required=True)

    p_props_compare = props_sub.add_parser(
        "compare", help="Check current props against past games vs. the same opponent"
    )
    p_props_compare.add_argument("--props", required=True, help="Path to a props CSV (see player_props.py docstring)")
    p_props_compare.add_argument("--logs", required=True, help="Path to a player game-log CSV")
    p_props_compare.add_argument("--team", default=None, help="Only show props for players on this team")
    p_props_compare.set_defaults(func=_cmd_props_compare)

    p_props_log = props_sub.add_parser(
        "log", help="Record a finished game's stat line (turns a settled prop into history)"
    )
    p_props_log.add_argument("--player", required=True)
    p_props_log.add_argument("--team", required=True)
    p_props_log.add_argument("--opponent", required=True)
    p_props_log.add_argument("--date", required=True, help="ISO date, e.g. 2025-09-14")
    p_props_log.add_argument("--stat-type", required=True, dest="stat_type")
    p_props_log.add_argument("--value", type=float, required=True, help="What actually happened")
    p_props_log.add_argument("--logs", required=True, help="Path to the game-log CSV to append to")
    p_props_log.set_defaults(func=_cmd_props_log)

    p_props_set = props_sub.add_parser(
        "set-line", help="Add or update this week's prop line for a player+opponent+stat"
    )
    p_props_set.add_argument("--player", required=True)
    p_props_set.add_argument("--team", required=True)
    p_props_set.add_argument("--opponent", required=True)
    p_props_set.add_argument("--stat-type", required=True, dest="stat_type")
    p_props_set.add_argument("--line", type=float, required=True)
    p_props_set.add_argument("--props", required=True, help="Path to the props CSV to update")
    p_props_set.set_defaults(func=_cmd_props_set_line)

    p_props_remove = props_sub.add_parser(
        "remove-line", help="Remove a prop that's no longer on this week's slate"
    )
    p_props_remove.add_argument("--player", required=True)
    p_props_remove.add_argument("--team", required=True)
    p_props_remove.add_argument("--opponent", required=True)
    p_props_remove.add_argument("--stat-type", required=True, dest="stat_type")
    p_props_remove.add_argument("--props", required=True, help="Path to the props CSV to update")
    p_props_remove.set_defaults(func=_cmd_props_remove_line)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
