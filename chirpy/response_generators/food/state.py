from typing import Optional

from chirpy.core.response_generator.state import *

@dataclass
class State(BaseState):
    cur_food: Optional['WikiEntity'] = None
    cur_supernode: Optional = None

@dataclass
class ConditionalState(BaseConditionalState):
    cur_food: Optional['WikiEntity'] = NO_UPDATE
    cur_supernode: Optional = NO_UPDATE
    prompt_treelet: Optional[str] = NO_UPDATE
