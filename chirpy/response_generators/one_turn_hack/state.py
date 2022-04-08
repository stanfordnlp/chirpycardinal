from chirpy.core.response_generator import BaseState, BaseConditionalState
from dataclasses import dataclass


@dataclass
class State(BaseState):
    talked_about_blm: bool = False

@dataclass
class ConditionalState(BaseConditionalState):
    talked_about_blm: bool = False
