from typing import List
from chirpy.response_generators.opinion2.state_actions import Action, State, AdditionalFeatures
from chirpy.response_generators.opinion2.abstract_policy import Policy


class TwoTurnAgreePolicy(Policy):

    def __repr__(self) -> str:
        return "TwoTurnAgreePolicy"

    def agree_reason_agree(self, state : State, action_space : List[Action]):
        action = Action(sentiment=state.cur_sentiment, give_agree=True, give_reason=True, solicit_agree=True)
        if action not in action_space:
            action = Action(exit=True)
        return action

    def get_action(self, state : State, action_space : List[Action], additional_features : AdditionalFeatures) -> Action:
        """On a high level, this policy first disagree with the user softly, then switch
        to a different entity and completely agree with the user.

        :param state: [description]
        :type state: State
        :param action_space: [description]
        :type action_space: List[Action]
        :param additional_features: [description]
        :type additional_features: AdditionalFeatures
        :return: [description]
        :rtype: Action
        """
        action = Action(exit=True)
        if len(state.action_history) == 0:
            user_sentiment_history = dict(state.user_sentiment_history)
            if state.cur_phrase not in user_sentiment_history:
                return Action(solicit_opinion=True)
            else:
                return Action(solicit_reason=True)
        prev_action = state.action_history[-1]
        if prev_action.solicit_opinion or prev_action.suggest_alternative:
            if state.cur_sentiment == 2:
                action = Action(exit=True)
            elif additional_features.detected_user_gave_reason:
                action = self.agree_reason_agree(state, action_space)
            else:
                action = Action(solicit_reason=True)
        elif prev_action.solicit_reason:
            if not additional_features.detected_user_disinterest:
                action = self.agree_reason_agree(state, action_space)
        return action
