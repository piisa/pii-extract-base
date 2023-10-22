"""
Context processing
"""

import regex

from typing import Tuple, List, Dict, Union

from ..defs import LANG_ANY
from .exception import InvArgException
from .normalizer import normalize


# Default width around a Pii value where context is searched for
DEFAULT_CONTEXT_WIDTH = 64

# Normalization options used when processing context prototypes
CONTEXT_NORM_OPTIONS = dict(whitespace=True, lowercase=True)


def _norm(ctx: str, lang: str, escape: bool = False) -> str:
    """
    Normalize a context string
     :param escape: escape regex metacharacters in string
    """
    ctx = normalize(ctx, lang, **CONTEXT_NORM_OPTIONS)
    if escape:
        ctx = regex.escape(ctx)
    return ctx


def context_spec(spec: Union[str, List, Dict], lang=str) -> Dict:
    """
    Parse & standardize a context specification
    """
    if spec is None:
        raise InvArgException("no context spec")

    # Simplified forms
    if isinstance(spec, str):
        spec = [spec]
    for s in spec:
        if not s:
            raise InvArgException("empty context spec")
    if isinstance(spec, list):
        return {
            "value": [_norm(c, lang) for c in spec],
            "width": [DEFAULT_CONTEXT_WIDTH, DEFAULT_CONTEXT_WIDTH],
            "regex": False,
        }

    out = {}

    # Sanitize value
    value = spec.get("value")
    if value is None:
        raise InvArgException("invalid context spec: {}", spec)
    if isinstance(value, str):
        value = [value]
    for s in value:
        if not s:
            raise InvArgException("empty context spec")

    # Get & process context type
    ctype = spec.get("type", "string")
    if ctype == "string":
        out["regex"] = False
        value = [_norm(v, lang) for v in value]
    elif ctype == "word":
        out["regex"] = True
        value = [regex.compile(r"\b" + _norm(v, lang, True) + r"\b") for v in value]
    elif ctype == "regex":
        out["regex"] = True
        value = [regex.compile(v, flags=regex.X) for v in value]
    else:
        raise InvArgException("invalid context type: {}", ctype)

    out["value"] = value

    # Get context width
    width = spec.get("width")
    if width is None:
        width = (DEFAULT_CONTEXT_WIDTH, DEFAULT_CONTEXT_WIDTH)
    elif isinstance(width, int):
        width = (width, width)
    elif len(width) == 1:
        width = (width[0], width[0])
    out["width"] = width

    return out


def context_check(text: str, context_spec: Dict, pii_pos: Tuple[int],
                  debug: bool = False) -> bool:
    """
    Try to locate any of a list of context candidate elements in a chunk of a
    text string (around a center given by the position of a PII element)
    """
    # Sanitize positions
    width = context_spec["width"]
    if isinstance(pii_pos, int):
        pii_pos = (pii_pos, pii_pos)
    elif len(pii_pos) == 1:
        pii_pos.append(pii_pos[0])

    # Extract context before and/or after the entity
    if width[0]:
        src1 = normalize(text[:pii_pos[0]], whitespace=True)
        start = max(len(src1) - width[0], 0)
        src = src1[start:]
    else:
        src = ""

    if width[1]:
        src2 = normalize(text[pii_pos[1]:], whitespace=True)
        if src:
            src += " "
        src += src2[:width[1]]

    if debug:
        print(f"... context (rgx={context_spec['regex']}): [{src}]")

    # Match
    if context_spec["regex"]:
        return any(c.search(src) for c in context_spec["value"])
    else:
        return any(c in src for c in context_spec["value"])
