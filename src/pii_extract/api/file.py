"""
File-based API
"""

import sys
from textwrap import TextWrapper

from typing import Dict, List, TextIO

from pii_data.helper.exception import InvArgException
from pii_data.helper.io import openfile, base_extension
from pii_data.helper.config import load_config
from pii_data.types.doc.localdoc import LocalSrcDocumentFile

from ..helper.types import TYPE_STR_LIST
from ..defs import FMT_CONFIG_PLUGIN, FMT_CONFIG_TASKS
from . import PiiProcessor


def print_tasks(langlist: List[str], proc: PiiProcessor, out: TextIO):
    """
    Print out the list of built tasks
    """
    tw = TextWrapper(initial_indent="     ", subsequent_indent="     ", width=78)
    print(f". Built tasks [language={','.join(langlist)}]", file=out)
    for (pii, subtype), tasklist in proc.task_info().items():
        print(f"\n {pii.name}   {subtype if subtype else ''}", file=out)
        for n, (lang, country, name, doc) in enumerate(tasklist):
            if n:
                print(file=out)
            print(f"   Language: {lang}", file=out)
            print(f"   Country: {country}", file=out)
            print(f"   Name: {name}", file=out)
            if doc:
                for ln in doc.splitlines():
                    print(tw.fill(ln), file=out)


def print_stats(stats: Dict[str, Dict], out: TextIO):
    """
    Print out statistics for the detection process
    """
    print("\n. Statistics:", file=out)
    for name, vd in stats.items():
        print("..", name, file=out)
        for k, v in vd.items():
            print(f"   {k:20} :  {v:5}", file=sys.stderr)


def piic_format(filename: str) -> str:
    """
    Find out the desired file format for a PII Collection
    """
    ext = base_extension(filename)
    if ext == ".json":
        return "json"
    elif ext in (".ndjson", ".jsonl"):
        return "ndjson"
    else:
        raise InvArgException("cannot recognize piic output format for: {}",
                              filename)

# ----------------------------------------------------------------------


def process_file(infile: str,
                 outfile: str,
                 configfile: TYPE_STR_LIST = None,
                 skip_plugins: bool = False,
                 lang: str = None,
                 country: List[str] = None,
                 tasks: List[str] = None,
                 chunk_context: bool = False,
                 outfmt: str = None,
                 debug: bool = False,
                 show_tasks: bool = False,
                 show_stats: bool = False) -> Dict:
    """
    Process a number of PII tasks on a file holding a source document
      :param infile: input source document
      :param outfile: output file where to store the detected PII entities
      :param configfile: JSON configuration file(s) to add (defining plugins
         and/or tasks)
      :param skip_plugins: skip loading pii-extract task plugins
      :param lang: language the document is in (if not defined inside the doc)
      :param country: countries to build tasks for (if None, all applicable
         countries for the language are used)
      :param tasks: specific set of PII tasks to build (default is all
         applicable tasks)
      :param chunk_context: when iterating the document, generate contexts
         for each chunk
      :param outfmt: format for the output list of tasks: "json" or "ndjson"

      :return: a dictionary with stats on the detection
    """
    # Load document and define the language
    doc = LocalSrcDocumentFile(infile)
    meta = doc.metadata
    lang = meta.get("main_lang") or meta.get("lang") or lang
    if not lang:
        raise InvArgException("no language defined in options or document")

    # Load config, if given
    if configfile:
        fmts = FMT_CONFIG_PLUGIN, FMT_CONFIG_TASKS
        config = load_config(configfile, formats=fmts)
    else:
        config = None

    # Create the object
    proc = PiiProcessor(skip_plugins=skip_plugins, config=config, debug=debug)

    # Build the task objects
    proc.build_tasks(lang, country, pii=tasks)
    if show_tasks:
        print_tasks(lang, proc, sys.stderr)

    if outfmt is None:
        outfmt = piic_format(outfile)

    if debug:
        print(". Reading from:", infile, file=sys.stderr)
        print(". Writing to:", outfile, file=sys.stderr)

    # Process the file
    piic = proc(doc, chunk_context=chunk_context)

    # Dump results
    with openfile(outfile, "wt") as fout:
        piic.dump(fout, format=outfmt)

    stats = proc.get_stats()
    if show_stats:
        print_stats(stats, sys.stderr)

    return stats
