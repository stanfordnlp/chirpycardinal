from chirpy.core.response_generator.state import *

@dataclass
class State(BaseState):
    used_neural_fallback_response: int = 0

@dataclass
class ConditionalState(BaseConditionalState):
    pass

