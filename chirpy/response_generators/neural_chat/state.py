import logging
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Set
from collections import defaultdict
from enum import Enum, auto

logger = logging.getLogger('chirpylogger')

@dataclass
class UserLabel:
    """A neural chat user response can have multiple or none of these labels"""
    NEG_NAV = 'NEG_NAV'  # when the user utterance was labeled as neg nav so we're stopping
    POS_NAV = 'POS_NAV'  # when the user gave posnav intent to talk about something else
    CHANGED_ENTITY = 'CHANGED_ENTITY'  # when the user utterance changed entity so we're stopping
    USER_TOPIC_UNFOUND = 'USER_TOPIC_UNFOUND'  # when the user topic was unfound so we're stopping
    OFFENSIVE = 'OFFENSIVE'  # when the user utterance is offensive
    RETURN_Q = 'RETURN_Q'  # when the user is asking the return question

@dataclass
class BotLabel:
    """A neural chat response/prompt can have multiple or none of these labels"""
    FALLBACK = 'FALLBACK'  # when the bot response is the handwritten fallback
    TECH_ERROR = 'TECH_ERROR'  # when we had a technical error getting gpt2 response
    RETURN_ANS = 'RETURN_ANS'  # when we are using the handwritten return answer
    GPT2ED = 'GPT2ED'  # when we are using a gpt2-generated response
    HANDOVER = 'HANDOVER'  # when neural chat is ending the conversation by providing some utterance
    NOT_CHOSEN = 'NOT_CHOSEN'  # when the bot response/prompt was not chosen


class ConditionalState(object):

    def __init__(self, next_treelet: Optional[str], most_recent_treelet: Optional[str] = None,
                 user_utterance: Optional[str] = None, user_labels: List[str] = [],
                 bot_utterance: Optional[str] = None, bot_labels: List[str] = []):
        """
        @param next_treelet: the name of the treelet we should run on the next turn if our response/prompt is chosen. None means turn off next turn.
        @param most_recent_treelet: the name of the treelet that handled this turn, if applicable
        @param user_utterance: the user's utterance on the current turn, if applicable
        @param user_labels: List of labels (strings) that apply to this user utterance
        @param bot_utterance: the neural chat bot's utterance on the current turn, if applicable
        @param bot_labels: List of labels (strings) that apply to this bot utterance
        """
        # Validate
        assert user_utterance is None or isinstance(user_utterance, str), "user_utterance should be a string"
        assert bot_utterance is None or isinstance(bot_utterance, str), "bot_utterance should be a string"
        if bot_utterance is not None:
            assert user_utterance is not None, "if bot_utterance is not None, user_utterance should not be None"
        assert all(isinstance(l, str) for l in user_labels), "user_labels should be strings"
        assert all(isinstance(l, str) for l in bot_labels), "bot_labels should be strings"
        assert (most_recent_treelet is not None) == (user_utterance is not None), "most_recent_treelet should be supplied iff user_utterance is supplied"

        # Save
        self.next_treelet = next_treelet
        self.most_recent_treelet = most_recent_treelet
        self.user_utterance = user_utterance
        self.user_labels = user_labels
        self.bot_utterance = bot_utterance
        self.bot_labels = bot_labels

    def __repr__(self):
        return f"<ConditionalState: next_treelet={self.next_treelet}, user_utterance={self.user_utterance}, " \
               f"user_labels={self.user_labels}, bot_utterance={self.bot_utterance}, bot_labels={self.bot_labels}, " \
               f"most_recent_treelet={self.most_recent_treelet}>"


class ConvHistory(object):
    def __init__(self):
        self.utterances = []  # list of strings, starting with user utterance
        self.labels = []  # list same length as self.utterance. each element is a list of UserUtteranceLabels or BotUtteranceLabels
        self.trigger_phrases_mentioned = {}  # dict mapping from trigger phrase (str) to (turn_num: int, the most recent turn on which the trigger phrase was mentioned, and posnav: bool, whether it was mentioned with PosNav intent)

    def add_mentioned_trigger_phrase(self, trigger_phrase: str, turn_num: int, posnav: bool):
        logger.debug(f"In ConvHistory, adding mentioned trigger_phrase={trigger_phrase} on turn_num={turn_num} with posnav={posnav}")
        self.trigger_phrases_mentioned[trigger_phrase] = (turn_num, posnav)

    @property
    def most_recent_trigger(self) -> Tuple[Optional[str], Optional[int], Optional[bool]]:
        """
        Determines the most recent mentioned trigger_phrase (preferring any that was mentioned with posnav intent), and returns:
            trigger_phrase: str. the trigger phrase that was mentioned
            turn_num: int. the turn on which it was mentioned
            posnav: bool. whether it was mentioned with PosNav intent
        """
        trigger_phrases_mentioned = sorted([(trigger_phrase, turn_num, posnav) for trigger_phrase, (turn_num, posnav) in self.trigger_phrases_mentioned.items()],
                                           key=lambda x: (x[1], x[2]), reverse=True)
        if trigger_phrases_mentioned:
            return trigger_phrases_mentioned[0]
        else:
            return None, None, None

    def update(self, conditional_state: ConditionalState):
        """Update the ConvHistory w.r.t. the ConditionalState"""
        if conditional_state.user_utterance is not None:
            self.utterances.append(conditional_state.user_utterance)
            self.labels.append(conditional_state.user_labels)
        if conditional_state.bot_utterance is not None:
            self.utterances.append(conditional_state.bot_utterance)
            self.labels.append(conditional_state.bot_labels)
        assert len(self.utterances) == len(self.labels), "self.utterances and self.labels should be the same length"

    @property
    def used_bot_labels(self) -> Set[str]:
        """A set of all the bot labels so far"""
        return {l for idx in range(1, len(self.labels), 2) for l in self.labels[idx]}

    def __repr__(self):
        return f"<ConvHistory: utterances={self.utterances}, labels={self.labels}, trigger_phrases_mentioned={self.trigger_phrases_mentioned}>"


class State(object):

    def __init__(self, next_treelet: Optional[str] = None, conv_histories: dict = {}):
        self.next_treelet = next_treelet  # the name of the treelet we should run on the next turn. None means turn off next turn.
        self.conv_histories = conv_histories  # Maps from treelet name (str) to ConvHistory. If a treelet isn't in the dict, that means it has an empty ConvHistory (we don't store it to minimize size of this object)

    def __repr__(self):
        return f"<State: next_treelet={self.next_treelet}, conv_histories={self.conv_histories}>"

    def treelet_has_been_used(self, treelet_name: str) -> bool:
        """Returns True iff this treelet has already spoken"""
        if treelet_name not in self.conv_histories:
            return False
        else:
            return len(self.conv_histories[treelet_name].utterances) > 0

    @property
    def used_bot_labels(self) -> Set[str]:
        """A set of all the bot labels so far, across all treelets"""
        return {l for convhistory in self.conv_histories.values() for l in convhistory.used_bot_labels}

    def add_mentioned_trigger_phrase(self, treelet_name: str, trigger_phrase: str, turn_num: int, posnav: bool):
        """Add the mentioned trigger phrase to the ConvHistory for treelet_name"""
        logger.debug(f"In state, adding mentioned trigger_phrase={trigger_phrase} on turn_num={turn_num} with posnav={posnav} for treelet_name={treelet_name}")
        if treelet_name not in self.conv_histories:
            self.conv_histories[treelet_name] = ConvHistory()
        self.conv_histories[treelet_name].add_mentioned_trigger_phrase(trigger_phrase, turn_num, posnav)

    def update_conv_history(self, conditional_state: ConditionalState):
        """Update the conversational history according to the ConditionalState"""
        most_recent_treelet = conditional_state.most_recent_treelet
        if most_recent_treelet:
            if most_recent_treelet not in self.conv_histories:
                self.conv_histories[most_recent_treelet] = ConvHistory()
            self.conv_histories[most_recent_treelet].update(conditional_state)

    def update_if_chosen(self, conditional_state: ConditionalState):
        """If our response/prompt has been chosen, update state using conditional state"""

        # Set the next_treelet for the next turn
        self.next_treelet = conditional_state.next_treelet

        # Update the ConvHistory for most_recent_treelet
        self.update_conv_history(conditional_state)


    def update_if_not_chosen(self, conditional_state: ConditionalState):
        """If our response/prompt has not been chosen, update state"""

        # Set the next_treelet for the next turn to be None (off)
        self.next_treelet = None

        # If there is a neural chat bot response, mark it as NOT_CHOSEN i.e. not delivered to the user
        if conditional_state.bot_utterance is not None:
            conditional_state.bot_labels.append(BotLabel.NOT_CHOSEN)

        # If this ConditionalState represents the start of the conversation, do nothing.
        # Otherwise, it represents the (not-chosen) continuation of a conversation, so update the ConvHistory for most_recent_treelet
        if self.treelet_has_been_used(conditional_state.most_recent_treelet):  # if it's a continuation
            self.update_conv_history(conditional_state)  # update

