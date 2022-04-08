from chirpy.core.response_generator.state import *

@dataclass
class State(BaseState):
    personal_issue_score: int = 0
    question_last_turn: bool = False
    neural_last_turn: bool = False

@dataclass
class ConditionalState(BaseConditionalState):
    personal_issue_score: int = NO_UPDATE
    question_last_turn: bool = False
    neural_last_turn: bool = False
