from dataclasses import dataclass
from chirpy.core.response_generator.state import BaseState, BaseConditionalState, NO_UPDATE

###
# Define the state that will be returned by all treelets
###
@dataclass
class State(BaseState):
    has_just_asked_to_exit: bool = False

@dataclass
class ConditionalState(BaseConditionalState):
    has_just_asked_to_exit: bool = False
