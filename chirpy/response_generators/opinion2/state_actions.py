from chirpy.response_generators.opinion2.utils import is_high_prec_neutral
from chirpy.response_generators.opinion2.opinion_sql import Phrase
import random
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger('chirpylogger')

@dataclass(frozen=False)
class Action:
    # First, decide our sentiment on the entity
    sentiment : int = 2 # Right now, only have 0 - dislike, 2 - neutral, and 4 - like
    # Then, decide whether we want to say agree or disagree
    give_agree : bool = False
    # Then, decide whether we want to give a reason or not
    give_reason : bool = False
    # Then, decide whether
    solicit_opinion : bool = False
    solicit_disambiguate : bool = False
    solicit_agree : bool = False
    solicit_reason : bool = False
    suggest_alternative : bool = False
    # This is a field indicating whether we should exit the conversation
    exit : bool = False
    hard_exit : bool = False
    # These are fields used for engineering purposes
    text : str = ''

    def __eq__(self, o: object) -> bool:
        if o.__class__ is not self.__class__:
            raise NotImplementedError
        return (self.sentiment, self.give_agree, self.give_reason, self.solicit_opinion, \
                self.solicit_disambiguate, self.solicit_agree, self.solicit_reason, self.suggest_alternative, self.exit) == \
                (o.sentiment, o.give_agree, o.give_reason, o.solicit_opinion, \
                 o.solicit_disambiguate, o.solicit_agree, o.solicit_reason, o.suggest_alternative, o.exit) # type: ignore

@dataclass(frozen=False)
class State:
    # Following properties are used for the policies
    detected_opinionated_phrases : Tuple[str, ...] = () # a running history of phrases detected
    utterance_history : Tuple[Tuple[str, str], ...] = () # a history of bot and user utterances
    action_history : Tuple[Action, ...] = () # a history of actions that the bot took
    user_sentiment_history : Tuple[Tuple[str, int], ...] = () # A history of user sentiments.
    cur_sentiment : int = 2 # the sentiment of the user.
    cur_policy : str = ''
    major_change : str = 'DisagreeAgreeSwitchAgreePolicy phrasing bug fix'

    # Following properties are engineering specific to make the bot work
    latest_utterance : str = ''
    last_policy : str = '' # the latest policy we are using
    cur_phrase : str = '' # the phrase we are opinionating on
    phrases_done : Tuple[str, ...] = () # a list of phrases that we no longer wish to opinionate
    reasons_used : Tuple[Tuple[str, Tuple[str, ...]], ...] = () # a list of reasons we already used
    last_turn_select : bool = False
    last_turn_prompt : bool = False
    evaluated : bool = False
    num_turns_since_long_policy : int = 0 # default to 0 to trigger short convo in the beginning
    first_episode : bool = False

    def reset_state(self):
        return State(detected_opinionated_phrases=self.detected_opinionated_phrases,
            user_sentiment_history=self.user_sentiment_history,
            phrases_done=self.phrases_done,
            evaluated=self.evaluated,
            last_policy=self.last_policy,
            num_turns_since_long_policy=self.num_turns_since_long_policy,
            first_episode=self.first_episode)

@dataclass(frozen=False)
class AdditionalFeatures:
    detected_phrases : Tuple[str, ...] = ()
    current_posnav_phrases : Tuple[str, ...] = ()
    detected_yes : bool = False
    detected_no : bool = False
    detected_like : bool = False
    detected_dislike : bool = False
    detected_user_gave_reason : bool = False
    detected_user_sentiment_switch : bool = False
    detected_user_disinterest : bool = False


def next_state(state : State, utterance : str, additional_features : AdditionalFeatures, entity_tracker = None) -> Optional[State]:
    """This method advances the state to the next state, it

    1. selects a cur_phrase if there is one available. Otherwise it returns None because you cannot advance a state
       without a cur_phrase
    2. It populates the utterance history by adding the current utterance.
    3. It detects the user's sentiment via a variety of ways (depending on the utterance and action history)

    :param state: the current state
    :type state: State
    :param utterance: the utterance of the user
    :type utterance: str
    :param additional_features: additional features that can be utilized
    :type additional_features: AdditionalFeatures
    :return: a new state if we can advance it. Otherwise None
    :rtype: Optional[State]
    """
    new_state = State(**state.__dict__)
    user_sentiment_history = dict(state.user_sentiment_history)
    if state.cur_phrase == '':
        # A phrase is considered available if user did not have an opinion, or if user did, have a non-neutral opinion
        available_phrases = additional_features.detected_phrases + additional_features.current_posnav_phrases
        available_phrases = [phrase for phrase in available_phrases \
                if phrase not in user_sentiment_history or user_sentiment_history[phrase] != 2]

        # remove talked_finished items
        if entity_tracker is not None:
            logger.primary_info(f"Phrases are {available_phrases}")
            available_phrases = [phrase for phrase in available_phrases if not any(e.name == phrase for e in entity_tracker.talked_finished)]
        if len(available_phrases) == 0:
            return None
        # We give priority to phrases which user have already expressed an opinion about
        known_opinion_phrases = [phrase for phrase in available_phrases if phrase in user_sentiment_history]
        if len(known_opinion_phrases) > 0:
            new_state.cur_phrase = random.choice(known_opinion_phrases)
            new_state.cur_sentiment = user_sentiment_history[new_state.cur_phrase]
        else:
            new_state.cur_phrase = random.choice(available_phrases)
    if state.latest_utterance != '':
        new_state.utterance_history += ((state.latest_utterance, utterance), )
    if len(state.action_history) > 0 and (state.action_history[-1].solicit_opinion or state.action_history[-1].suggest_alternative):
        sentiment = 2
        if is_high_prec_neutral(utterance):
            sentiment = 2
        elif additional_features.detected_dislike and not additional_features.detected_like:
            sentiment = 0
        elif additional_features.detected_like and not additional_features.detected_dislike:
            sentiment = 4
        elif additional_features.detected_yes:
            sentiment = 4
        elif additional_features.detected_no:
            sentiment = 0
        new_state.user_sentiment_history += ((state.cur_phrase, sentiment), )
        new_state.cur_sentiment = sentiment
    new_state.latest_utterance = ''
    return new_state

def fill_state_on_action(state_p : State, action : Action, text : str,
        phrase : str, additional_features : AdditionalFeatures, reason : Optional[str],
        opinionable_phrases : Dict[str, Phrase],
        opinionable_entities : Dict[str, List[Phrase]]) -> State:
    """This is a convenient function that fill the state after an action is generated. Specifically it

    1. adds the current action to the history
    2. adds the phrase to a list of phrases done so we don't prompt it again
    3. sets the cur_phrase and cur_sentiment correctly conditioned on the action
    4. adds the reason to a list of reasons used

    :param state_p: the state we are modifying
    :type state_p: State
    :param action: the action that the policy returned
    :type action: Action
    :param text: the text that was generated by the utterancify
    :type text: str
    :param phrase: the phrase we are currently opinionating
    :type phrase: str
    :param additional_features: the additional features we populated earlier
    :type additional_features: AdditionalFeatures
    :param reason: the reason we used in this turn, or None if we didn't use any
    :type reason: Optional[str]
    :return: a new state. Note that this function modifies the state passed in.
    :rtype: State
    """
    state_p.latest_utterance = text
    state_p.action_history += (action,)
    if state_p.cur_phrase != '' and state_p.cur_phrase not in state_p.phrases_done:
        state_p.phrases_done += (state_p.cur_phrase, )
        entity_done = opinionable_phrases[state_p.cur_phrase].wiki_entity_name
        if entity_done is not None:
            state_p.phrases_done += tuple([phrase.text for phrase in opinionable_entities[entity_done]])
    if action.exit:
        state_p.cur_phrase = ''
        state_p.cur_sentiment = 2
    elif phrase != state_p.cur_phrase:
        state_p.cur_phrase = phrase
        state_p.cur_sentiment = 2
    if reason is not None:
        reasons_used = dict(state_p.reasons_used)
        if state_p.cur_phrase not in reasons_used:
            reasons_used[state_p.cur_phrase] = ()
        reasons_used[state_p.cur_phrase] += (reason, )
        state_p.reasons_used = tuple(reasons_used.items())
    return state_p
