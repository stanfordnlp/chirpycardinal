from typing import Dict, List
from chirpy.response_generators.opinion2.state_actions import Action, AdditionalFeatures, State

class Policy:
    
    def __repr__(self) -> str:
        raise NotImplementedError()
    
    def get_action(self, state : State, action_space : List[Action], additional_features : AdditionalFeatures) -> Action:
        raise NotImplementedError()

    def update_policy(self, episode : List[State], episode_features : List[Dict[str, int]], rewards : List[int]) -> None:
        return