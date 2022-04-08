from dataclasses import dataclass, field
from typing import Set
from chirpy.core.response_generator.state import *
###
# Define the state that will be returned by all treelets
###

@dataclass
class State(BaseState):
    entities_prompted: Set[str] = field(default_factory=set)

@dataclass
class ConditionalState(BaseConditionalState):
    entities_prompted: Set[str] = NO_UPDATE
    from_entity: Optional['WikiEntity'] = NO_UPDATE
