"""Command line entrypoint for operationbot"""
import argparse
import sys
from typing import Optional

from operationbot.main import main as bot_run

def parse_arguments(arguments: list[str]) -> argparse.Namespace:
    """Parse generic arguments, given as parameters"""
    parser = argparse.ArgumentParser(
        "operationbot",
        description="Operations bot for the Zeusops discord",
    )
    parser.add_argument("--config", help="Some extra config")
    return parser.parse_args(arguments)


def cli(arguments: Optional[list[str]] = None):
    """Run the operationbot cli"""
    if arguments is None:
        arguments = sys.argv[1:]
    args = parse_arguments(arguments)
    main(args.config)


def main(config):
    """Run the program's main command"""
    print(f"{config=}")
    bot_run()
