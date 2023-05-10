"""
Some utility functions/classes for raw task descriptor parsing
"""


from pii_data.helper.exception import InvArgException


class InvPiiTask(InvArgException):
    """
    An exception signaling an invalid Pii Task descriptor
    """
    pass
