from dataclasses import dataclass
from typing import List, Optional, Tuple, Set  # NOQA
from chirpy.core.response_generator.state import BaseState, BaseConditionalState, NO_UPDATE
from chirpy.response_generators.offensive_user.offensive_user_helpers import OFFENSE_KEY_TO_TYPE
###
# Define the state that will be returned by all treelets
###
@dataclass
class State(BaseState):
    used_offensiveuser_response_count: int = 0
    used_criticaluser_response_count: int = 0
    used_offensiveuser_response: bool = False
    used_criticaluser_response: bool = False
    experiment_configuration = None
    handle_response: bool = False
    followup = None
    offense_type = None
    handled_response: bool = False

    def __init__(self):
        self.offense_type_counts = {t: 0 for t in OFFENSE_KEY_TO_TYPE.values()}

@dataclass
class ConditionalState(BaseConditionalState):
    used_offensiveuser_response: bool = False
    used_criticaluser_response: bool = False
    experiment_configuration = NO_UPDATE
    handle_response: bool = False
    followup = NO_UPDATE
    offense_type = NO_UPDATE
    handled_response: bool = NO_UPDATE
