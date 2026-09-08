"""Command-line interface for the sports-betting toolkit."""

from __future__ import annotations

import argparse
import sys

from .arbitrage import find_arbitrage, arbitrage_stakes
from .ev import expected_value
from .kelly import kelly_fraction, kelly_stake
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
