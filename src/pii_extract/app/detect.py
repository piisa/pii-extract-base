"""
Command-line script to process source documents and detect PII instances
"""

import sys
import argparse

from typing import List

from .. import VERSION
from ..api import process_file


def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"Perform PII detection on a document (version {VERSION})")

    g0 = parser.add_argument_group("Input/output paths")
    g0.add_argument("infile", help="source document")
    g0.add_argument("outfile", help="destination file")

    g1 = parser.add_argument_group("Language specification")
    g1.add_argument("--lang", help="set document language")
    g1.add_argument("--country", nargs="+", help="countries to use")

    g2 = parser.add_argument_group("Task specification")
    g2.add_argument("--configfile", "--config", nargs="+",
                    help="add pii tasks and/or plugins defined in JSON files")
    g2.add_argument("--skip-plugins", action="store_true",
                    help="do not load pii-extract plugins")
    g2.add_argument("--tasks", nargs="+", metavar="TASK_TYPE",
                    help="limit the set of pii tasks to include")

    g2 = parser.add_argument_group("Processing options")
    g2.add_argument("--chunk-context", action="store_true",
                    help="when iterating over the document, add chunk contexts")

    g3 = parser.add_argument_group("Other")
    g3.add_argument("--show-stats", action="store_true", help="show statistics")
    g3.add_argument("--show-tasks", action="store_true", help="show defined tasks")
    g3.add_argument("--debug", action="store_true", help="debug mode")
    g3.add_argument('--reraise', action='store_true',
                    help='re-raise exceptions on errors')

    return parser.parse_args(args)


def main(args: List[str] = None):
    if args is None:
        args = sys.argv[1:]
    nargs = parse_args(args)
    args = vars(nargs)
    reraise = args.pop("reraise")
    try:
        process_file(args.pop("infile"), args.pop("outfile"), **args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if reraise:
            raise
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
