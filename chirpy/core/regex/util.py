"""This file is for generally useful regex patterns and functions"""

# This regex matches any string, including the empty string. The ? makes it non-greedy.
# Non-greedy means that it'll stop matching as soon as the next part of regex starts matching.
from typing import List

# This regex matches any string, including the empty string. The ? makes it non-greedy.
# Non-greedy means that it'll stop matching as soon as the next part of regex starts matching.
OPTIONAL_TEXT = '.*?'

# This regex matches any string, except the empty string. The ? makes it non-greedy.
NONEMPTY_TEXT = '.+?'

# This regex matches: (a) any string ending in space, and (b) empty string. The ? makes it non-greedy.
OPTIONAL_TEXT_PRE = '(.*? |)'

# This regex matches: (a) any string starting with space, and (b) empty string. The ? makes it non-greedy.
# Note: I (Abi) changed this from '( .*?|)' to '(| .*?)' because that gave the non-greedy behavior I wanted in one case,
# and all the regex tests are still passing, so it seems OK. Let me know if it's a problem.
OPTIONAL_TEXT_POST = '(| .*?)'

# This regex matches any non-empty string where the first character is a space and the last character is a space.
# The ? makes it non-greedy.
OPTIONAL_TEXT_MID = ' (.*? |)'

# Greedy versions of the above constants.
OPTIONAL_TEXT_GREEDY = '.*'
NONEMPTY_TEXT_GREEDY = '.+'
OPTIONAL_TEXT_PRE_GREEDY = '(.* |)'
OPTIONAL_TEXT_POST_GREEDY = '( .*|)'
OPTIONAL_TEXT_MID_GREEDY = ' (.*? |)'



def oneof(lst: List[str]) -> str:
    """Given a list of regex patterns, returns a regex pattern that matches any one in the list"""
    assert isinstance(lst, list)
    return '({})'.format('|'.join(lst))


def one_or_more_spacesep(lst: List[str]):
    """
    Given a list of regex patterns, returns a regex pattern that matches any string which is one or more items from
    the list, space-separated (no space at the start or end).
    """
    assert isinstance(lst, list)
    return f'({oneof(lst)})( {oneof(lst)})*'


def zero_or_more_spacesep(lst: List[str]):
    """
    Given a list of regex patterns, returns a regex pattern that matches any string which is zero or more items from
    the list, space-separated (no space at the start or end).
    """
    assert isinstance(lst, list)
    return '({oneof(lst)})?( {oneof(lst)})*'
