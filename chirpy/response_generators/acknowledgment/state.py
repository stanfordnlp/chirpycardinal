from dataclasses import dataclass, field
from typing import List
from chirpy.core.response_generator.state import BaseState, BaseConditionalState, NO_UPDATE

###
# Define the state that will be returned by all treelets
###
@dataclass
class State(BaseState):
    acknowledged_entities: List[str] = field(default_factory=list)

@dataclass
class ConditionalState(BaseConditionalState):
    acknowledged_entities: List[str] = NO_UPDATE
