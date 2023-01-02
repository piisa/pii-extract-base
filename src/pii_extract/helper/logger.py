"""
A logger dispatcher class
"""

import sys
import logging

from typing import Union


class Dummy:
    """
    Do-nothing logger
    """
    def __getattr__(self, name):
        return self.dummy

    def dummy(self, *args, **kwargs):
        pass

    def __repr__(self) -> str:
        return "<PII DummyLogger>"


class StdLogger:
    """
    Route logging messages through the standard Python logger
    """

    def __init__(self, name: str, level: int):
        self._log = logging.getLogger(name)
        self._log.setLevel(level)

    def __call__(self, msg, *args, level: int = logging.INFO, **kwargs):
        self._log.log(level, msg, *args, **kwargs)

    def __repr__(self) -> str:
        return f"<PII StdLogger level={self._log.getEffectiveLevel()}>"


class DebugLogger:
    """
    Print logging messages to standard error
    """

    def __call__(self, msg, *args, level: int = logging.INFO, **kwargs):
        if args:
            msg = msg % args
        file = kwargs.pop("file", sys.stderr)
        print(msg, file=file, **kwargs)

    def __repr__(self) -> str:
        return "<PII DebugLogger>"

# -----------------------------------------------------------------------

class PiiLogger:
    """
    The dispatcher class
    """

    def __new__(cls, name: str, debug: Union[bool, int] = None):
        """
         :param name: the logger name, to be used for standard Python logging
         :param debug: behaviour
            - `None`: ignore all messages
            - `True`: print out messages to standard error
            - a logging level: route all messages through Python logging
        """
        if debug is None:
            return Dummy()
        elif debug is True:
            return DebugLogger()
        else:
            return StdLogger(name, level=debug)
