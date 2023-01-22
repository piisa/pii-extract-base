"""
A simple text normalization function
"""
from ..defs import LANG_ANY

def normalize(text: str, lang: str = LANG_ANY,
              whitespace: bool = False, lowercase: bool = False) -> str:
    """
    Perforn some normalization steps on a text string
      :param text: the string to normalize
      :param lang: language the string is in, if available. CURRENTLY UNUSED
      :param whitespace: normalize spaces
      :param lowercase: lowercase the string
    """
    if whitespace:
        text = " ".join(text.split())

    if lowercase:
        text = text.lower()

    return text
