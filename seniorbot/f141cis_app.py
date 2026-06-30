"""Dedicated executable entry point for the F141CIS export."""

from __future__ import annotations

import sys

from seniorbot.cli import main


DEFAULT_ARGS = [
    "f141cis",
    "--serie",
    "036",
    "--cfops",
    "5101",
    "5102",
    "6101",
    "6102",
    "5910",
    "6910",
    "--output",
    r"C:\Temp\f141cis.xlsx",
]


def run() -> int:
    """Run F141CIS with the default business parameters."""

    args = sys.argv[1:] or DEFAULT_ARGS
    if args and args[0] != "f141cis":
        args = ["f141cis", *args]
    return main(args)


if __name__ == "__main__":
    raise SystemExit(run())
