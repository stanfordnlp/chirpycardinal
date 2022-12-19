from dataclasses import dataclass, field
from typing import Any, List, Tuple, Set, Optional, Dict  # NOQA

from chirpy.core.response_generator.response_type import ResponseType

import os
import logging
logger = logging.getLogger('chirpylogger')

"""
Define the base states that will be returned by all treelets.
Individual RGs should implement a state.py that defines their own State and ConditionalState 
that inherit from these classes.

For no update to be made, set the conditional state's attribute values to NO_UPDATE.
"""

NO_UPDATE = "no-update"

import yaml
BASE_PATH = os.path.join(os.path.dirname(__file__), '../../symbolic_rgs')
with open(os.path.join(BASE_PATH, 'state.yaml')) as f:
    ALL_STATE_KEYS = yaml.safe_load(f)

@dataclass
class BaseState:
    prev_treelet_str: str = ''
    next_treelet_str: Optional[str] = ''
    response_types: Tuple[str] = ()
    num_turns_in_rg: int = 0

@dataclass
class BaseConditionalState:
    prev_treelet_str: str = ''
    next_treelet_str: Optional[str] = ''
    response_types: Tuple[str] = NO_UPDATE

def construct_response_types_tuple(response_types):
    return tuple([str(x) for x in response_types])

@dataclass
class BaseSymbolicState:
    prev_treelet_str: str = ''
    next_treelet_str: Optional[str] = ''
    response_types: Tuple[str] = ()
    num_turns_in_rg: int = 0
    cur_supernode: str = ''
    data: Dict[str, Any] = field(default_factory=dict)
    turns_history: Dict[str, int] = field(default_factory=dict)
    
    def __getitem__(self, key):
        assert key in ALL_STATE_KEYS
        logger.warning(f"Looking up value for {key}, data keys are {self.data}, all_state_keys are {ALL_STATE_KEYS}")
        return self.data.get(key, ALL_STATE_KEYS[key])
        
    def __setitem__(self, key, new_value):
        assert key in ALL_STATE_KEYS
        self.data[key] = new_value
        
    def update(self, data):
        for key in data:
            assert key in ALL_STATE_KEYS, f"Key not found: {key}"    
        self.data.update(data)
        
@dataclass
class BaseSymbolicConditionalState:
    prev_treelet_str: str = ''
    next_treelet_str: Optional[str] = ''
    cur_supernode: str = NO_UPDATE
    response_types: Tuple[str] = NO_UPDATE
    data: Dict[str, Any] = NO_UPDATE