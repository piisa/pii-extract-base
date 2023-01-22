"""
Utilities for managing field values
"""

from typing import Dict, Union, Set, List, Iterable


def union_sets(values: Iterable[Set[str]]) -> List[str]:
    """
    Given an iterable of sets, return the union of all of their values, as
    a sorted list
    """
    all_values = set().union(*values)
    return sorted(all_values)


def field_set(value: Union[str, Iterable[str], None]) -> Set[str]:
    """
    Return a (possibly multiple) field as a set of values
    """
    return set([value] if isinstance(value, str) else value) if value else set()


def taskd_field(taskd: Dict, field: str = "lang") -> Set[str]:
    """
    Get the a field from a descriptor dictionary
     :param taskd: the task descriptor dictionary
     :param field: the field to fetch
     :param as_set: return it as a set of values
     :return: a set of field values
    """
    if isinstance(taskd, dict):
        lang = taskd.get(field)
        return field_set(lang)
    else:
        allsets = (taskd_field(s, field) for s in taskd)
        return set().union(*allsets)
