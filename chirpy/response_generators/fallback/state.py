from chirpy.core.response_generator.state import BaseState, BaseConditionalState, NO_UPDATE, dataclass


@dataclass
class State(BaseState):
    used_fallback_response: int = 0
    used_fallback_prompt: int = 0
    

@dataclass
class ConditionalState(BaseConditionalState):
    used_fallback_response: int = NO_UPDATE
    used_fallback_prompt: int = NO_UPDATE
