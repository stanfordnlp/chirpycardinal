from dataclasses import dataclass
from typing import List, Tuple, Set  # NOQA
from chirpy.core.response_generator.state import *
###
# Define the state that will be returned by all treelets
###

@dataclass
class State(BaseState):
    have_prompted: bool = False

@dataclass
class ConditionalState(BaseConditionalState):
    have_prompted: bool = NO_UPDATE

