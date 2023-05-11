"""
Command-line script to show information about available plugins,
languages & tasks
"""

import sys
import argparse
from textwrap import TextWrapper

from typing import List, TextIO

from pii_data.helper.config import load_config

from .. import VERSION
from ..gather.collection.sources import PluginTaskCollector
from ..api import PiiProcessor
from ..api.file import print_tasks


def print_plugins(args: argparse.Namespace, out: TextIO, debug: bool = False):
    """
    List the plugins
    """
    config = load_config(args.config) if args.config else None
    ptc = PluginTaskCollector(config=config, debug=debug)
    print(". Installed plugins", file=out)
    tw = TextWrapper(initial_indent="   ", subsequent_indent="   ")
    for plugin in ptc.list_plugins():
        print(f"\n Name: {plugin['name']}", file=out)
        print(f" Source: {plugin['source']}\n Version: {plugin['version']}   ",
              file=out)
        desc = plugin.get('description')
        if desc:
            print(" Description:", tw.fill(desc), sep="\n")


def print_languages(args: argparse.Namespace, out: TextIO):
    """
    Print available languages
    """
    config = load_config(args.config) if args.config else None
    proc = PiiProcessor(config=config, skip_plugins=args.skip_plugins,
                        debug=args.debug)
    print(". Defined languages")
    for lang in proc.language_list():
        print(f"  {lang}")


def task_info(args: argparse.Namespace, out: TextIO):
    """
    Show info about tasks
    """
    config = load_config(args.config) if args.config else None
    proc = PiiProcessor(config=config, skip_plugins=args.skip_plugins,
                        languages=args.lang, debug=args.debug)

    for lang in args.lang or [None]:
        proc.build_tasks(lang, args.country, pii=args.tasks,
                         add_any=not args.strict)

    print_tasks(args.lang, proc, out)


def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"Show information about usable PII tasks (version {VERSION})")

    opt_com1 = argparse.ArgumentParser(add_help=False)
    c3 = opt_com1.add_argument_group('Source loading options')
    c3.add_argument("--config", nargs="+",
                    help="PIISA configuration file(s) to load")
    c3.add_argument("--skip-plugins", action="store_true",
                    help="do not load pii-extract plugins")

    opt_com2 = argparse.ArgumentParser(add_help=False)
    c1 = opt_com2.add_argument_group('Task selection options')
    c1.add_argument("--lang", nargs="+", help="language(s) to select")
    c1.add_argument("--country", nargs="+", help="countries to select")
    c1.add_argument("--strict", action="store_true",
                    help="Include only tasks that comply strictly with selection")


    opt_com3 = argparse.ArgumentParser(add_help=False)
    c2 = opt_com3.add_argument_group("Other")
    c2.add_argument("--debug", action="store_true", help="debug mode")
    c2.add_argument('--reraise', action='store_true',
                    help='re-raise exceptions on errors')

    subp = parser.add_subparsers(help='command', dest='cmd')

    s0 = subp.add_parser("list-plugins", parents=[opt_com1, opt_com3],
                         help="List all installed pii-extract plugins")

    s1 = subp.add_parser('list-languages', parents=[opt_com1, opt_com3],
                         help="List all languages defined in tasks")

    s2 = subp.add_parser("list-tasks", parents=[opt_com1, opt_com2, opt_com3],
                         help="List available detection tasks")

    #g21 = g2.add_mutually_exclusive_group(required=True)
    s2.add_argument("--tasks", metavar="TASK_TYPE", nargs="+",
                    help="specific pii task types to include")

    parsed = parser.parse_args(args)
    if not parsed.cmd:
        parser.print_usage()
        sys.exit(1)
    return parsed


def main(args: List[str] = None):
    if args is None:
        args = sys.argv[1:]
    args = parse_args(args)

    try:
        if args.cmd == "list-plugins":
            print_plugins(args, sys.stdout)
        elif args.cmd == "list-languages":
            print_languages(args, sys.stdout)
        else:
            task_info(args, sys.stdout)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.reraise:
            raise
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
