from dataclasses import dataclass
from typing import Any, List, Tuple, Set, Optional, Dict  # NOQA

from chirpy.core.response_generator.response_type import ResponseType

from chirpy.core.entity_linker.entity_linker_classes import WikiEntity

import logging
logger = logging.getLogger('chirpylogger')

"""
Define the base states that will be returned by all treelets.
Individual RGs should implement a state.py that defines their own State and ConditionalState 
that inherit from these classes.

For no update to be made, set the conditional state's attribute values to NO_UPDATE.
"""

NO_UPDATE = "no-update"

@dataclass
class BaseState:
    prev_treelet_str: str = ''
    next_treelet_str: Optional[str] = ''
    response_types: Tuple[str] = ()
    num_turns_in_rg: int = 0
    archived_state: "BaseState" = None
    rg_that_was_taken_over: str = None
    takeover_entity: WikiEntity = None

@dataclass
class BaseConditionalState:
    prev_treelet_str: str = ''
    next_treelet_str: Optional[str] = ''
    response_types: Tuple[str] = NO_UPDATE
    archived_state: "BaseState" = NO_UPDATE
    rg_that_was_taken_over: str = NO_UPDATE
    takeover_entity: WikiEntity = NO_UPDATE

def construct_response_types_tuple(response_types):
    return tuple([str(x) for x in response_types])
