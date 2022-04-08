import chirpy.response_generators.opinion2.utils as utils
from typing import Dict, List
from chirpy.response_generators.opinion2.state_actions import AdditionalFeatures, State, Action
from chirpy.response_generators.opinion2.abstract_policy import Policy

class AlwaysAgreePolicy(Policy):
    
    def __repr__(self) -> str:
        return "AlwaysAgreePolicy"

    def get_agree_solicit_reason(self, state : State, action_space : List[Action]):
        action = Action(sentiment=state.cur_sentiment, give_agree=True, give_reason=True, solicit_reason=True)
        if action not in action_space:
            action = Action(solicit_reason=True)
        if action not in action_space:
            action = Action(exit=True)
        return action
    
    def get_agree_solicit_agree(self, state : State, action_space : List[Action]):
        action = Action(sentiment=state.cur_sentiment, give_agree=True, give_reason=True, solicit_agree=True)
        if action not in action_space:
            action = Action(suggest_alternative=True)
        if action not in action_space:
            action = Action(exit=True)
        return action

    def get_agree_suggest_alternative(self, state : State, action_space : List[Action]):
        action = Action(suggest_alternative=True)
        if action not in action_space:
            action = Action(suggest_alternative=True)
        if action not in action_space:
            action = Action(exit=True)
        return action

    def get_action(self, state : State, action_space : List[Action], additional_features : AdditionalFeatures) -> Action:
        """On a high level, this policy follows the following fixed trajectory

        1. Ask the user if they like the phrase or not (skip if we already have that info)
        2. Agree with the user, give a reason (if possible) and ask user's reason
        3. Give another reason (if possible) and ask if user agrees
        4. Switch to a different entity (if possible), and start over at stage 1
        
        :param state: the current state
        :type state: State
        :param action_space: a list of available actions
        :type action_space: List[Action]
        :param additional_features: additional features the policy can use
        :type additional_features: AdditionalFeatures
        :return: a specific action within the confines of the action spaces
        :rtype: Action
        """
        number_of_switches = len([action for action in state.action_history if action.suggest_alternative])
        action = Action(exit=True)
        if len(state.action_history) == 0: # First turn
            user_sentiment_history = dict(state.user_sentiment_history)
            if state.cur_phrase not in user_sentiment_history:
                action = Action(solicit_opinion=True)
            else:
                action = Action(solicit_reason=True)
                state.cur_sentiment = user_sentiment_history[state.cur_phrase]
        elif additional_features.detected_user_sentiment_switch and not state.action_history[-1].solicit_disambiguate:
            action = Action(exit=True)
        elif state.action_history[-1].solicit_disambiguate and additional_features.detected_no and state.cur_sentiment == 2:
            action = Action(exit=True)
        elif state.action_history[-1].sentiment != 2 and state.action_history[-1].sentiment != state.cur_sentiment:
            action = self.get_agree_solicit_reason(state, action_space)
        elif state.action_history[-1].solicit_opinion or state.action_history[-1].suggest_alternative \
                or state.action_history[-1].solicit_disambiguate:
            if state.cur_sentiment == 2:
                action = Action(exit=True)
            elif additional_features.detected_user_gave_reason:
                action = self.get_agree_solicit_agree(state, action_space)
            else:
                action = self.get_agree_solicit_reason(state, action_space)
        elif state.action_history[-1].solicit_reason:
            if not additional_features.detected_user_disinterest: # Check if user is still interested
                action = self.get_agree_solicit_agree(state, action_space)
        elif state.action_history[-1].solicit_agree:
            if number_of_switches == 0: # Check if user is still interested
                action = self.get_agree_suggest_alternative(state, action_space)
        return action

    def update_policy(self, episode: List[State], episode_features: List[Dict[str, int]], rewards : List[int]) -> None:
        return