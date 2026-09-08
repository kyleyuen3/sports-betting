"""Checks that the README's CLI commands table (and library usage example)
actually match what the CLI implements - so a new subcommand like
`bankroll leaderboard` can't silently go undocumented, or vice versa.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from sports_betting.cli import build_parser

README_PATH = Path(__file__).resolve().parent.parent / "README.md"


def _readme_text() -> str:
    return README_PATH.read_text()


def _subparsers_action(parser: argparse.ArgumentParser) -> argparse._SubParsersAction | None:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action
    return None


def _all_cli_commands() -> set[str]:
    """Every command the CLI actually exposes, e.g. "convert", "bankroll leaderboard"."""
    top_level = _subparsers_action(build_parser())
    assert top_level is not None, "CLI has no top-level subcommands"

    commands = set()
    for name, subparser in top_level.choices.items():
        nested = _subparsers_action(subparser)
        if nested is None:
            commands.add(name)
        else:
            commands.update(f"{name} {nested_name}" for nested_name in nested.choices)
    return commands


def _cli_table_section() -> str:
    match = re.search(r"## CLI commands\n(.*?)\n## ", _readme_text(), re.DOTALL)
    assert match, "Could not find the '## CLI commands' section in README.md"
    return match.group(1)


def _cli_table_commands() -> set[str]:
    """Command names listed in the README's '## CLI commands' table."""
    commands = set()
    for line in _cli_table_section().splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cell_match = re.match(r"\|\s*`([^`]+)`", line)
        if cell_match:
            commands.add(cell_match.group(1))
    return commands


def _library_usage_snippet() -> str:
    match = re.search(r"## Library usage\n\n```python\n(.*?)\n```", _readme_text(), re.DOTALL)
    assert match, "Could not find the library usage code block in README.md"
    return match.group(1)


def test_readme_has_cli_commands_table():
    assert "## CLI commands" in _readme_text()


def test_cli_table_lists_every_actual_command():
    documented = _cli_table_commands()
    actual = _all_cli_commands()
    assert documented, "No commands found in the README's CLI commands table"
    missing_from_readme = actual - documented
    stale_in_readme = documented - actual
    assert not missing_from_readme, f"CLI commands undocumented in README: {missing_from_readme}"
    assert not stale_in_readme, f"README documents commands the CLI no longer has: {stale_in_readme}"


def test_cli_table_includes_bankroll_leaderboard():
    assert "bankroll leaderboard" in _cli_table_commands()


def test_cli_table_includes_bankroll_export():
    assert "bankroll export" in _cli_table_commands()


def test_leaderboard_command_actually_exists_in_cli():
    assert "bankroll leaderboard" in _all_cli_commands()


def test_library_usage_example_mentions_leaderboard_and_export():
    snippet = _library_usage_snippet()
    assert "leaderboard(" in snippet
    assert "export_csv(" in snippet
