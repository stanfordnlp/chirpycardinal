import logging
import random
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyPrompt, ResponsePriority
from chirpy.response_generators.launch.launch_utils import Treelet, ConditionalState, State, UserIntent
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.core.regex.templates import MyNameIsTemplate, DoesNotWantToSayNameTemplate
from chirpy.core.regex.word_lists import YES
from chirpy.annotators.corenlp import Sentiment
from typing import Tuple, Optional
from chirpy.core.smooth_handoffs import SmoothHandoff
from chirpy.core.entity_linker.lists import get_unigram_freq

logger = logging.getLogger('chirpylogger')

GREET_WITH_NAME = [
    "Well it's nice to meet you, {}! I'm excited to chat with you today.",
    "Nice to meet you, {}! I'm looking forward to chatting with you today.",
    "Glad to meet you, {}! I appreciate you taking the time to chat with me today.",
]
GREET_WITHOUT_NAME = [
    "Great to meet you! Let's get to chatting!",
    "Nice to meet you! Let's get started!",
    "Glad to meet you! Let's get chatting!",
]
ASK_NAME_AGAIN = "Sorry, I didn't catch your name. Would you mind repeating it?"
ASK_NAME_FIRST_TIME = "Ok, great! What's your name?"
MOVING_ON = "No problem. Let's move on!"

class HandleNameTreelet(Treelet):

    def could_be_name(self, utterance):
        if len(utterance.split()) == 1:

            # If utterance is not in our high-frequency spoken unigrams (except for mark), then it may be a name
            if get_unigram_freq(utterance) == 0 or utterance == 'mark':
                return True

        return False

    def is_negative_user_sentiment(self):
        """Determines if user had negative response. Returns bool"""
        return self.state_manager.current_state.corenlp['sentiment'] == Sentiment.NEGATIVE or \
               self.state_manager.current_state.corenlp['sentiment'] == Sentiment.STRONG_NEGATIVE

    def get_name_from_utterance(self, user_utterance) -> Tuple[UserIntent, Optional[str]]:
        """Tries to get user's name from their utterance. Returns bool (if user wanted to give name) and the name (string) (or None)"""

        # Check if user explicitly said they did not want to tell us their name, or expressed a negative sentiment
        no_slots = DoesNotWantToSayNameTemplate().execute(user_utterance)
        if no_slots or self.is_negative_user_sentiment():
            logger.primary_info('Detected that user did not want to say name. Moving onto HOWDY conversation.')
            return UserIntent.no, None

        # Check if user asked us to repeat
        if "what" in user_utterance or "repeat" in user_utterance:
            return UserIntent.repeat, None

        # Check if user asked us why we want to know their name
        if "why" in user_utterance:
            return UserIntent.why, None

        # Next try matching with MyNameIs regex
        my_name_is_slots = MyNameIsTemplate().execute(user_utterance)
        if my_name_is_slots:
            # Try to get proper nouns from name slot:
            name_slot = my_name_is_slots['name'].split()
            proper_nouns = self.state_manager.current_state.corenlp['proper_nouns']
            if "alexa" in proper_nouns:
                proper_nouns.remove("alexa")
            intersection = list(set(name_slot) & set(proper_nouns))
            if len(intersection) > 0:
                name = intersection[0]
                logger.primary_info('Detected MyNameIsIntent with name_slot={} and proper nouns in name_slot={}. Choosing {} as name.'.format(name_slot, intersection, name))
                return UserIntent.yes, name

            # If no intersection, just use first word of name slot
            name = name_slot[0]
            logger.primary_info('Detected MyNameIsIntent with name_slot={}. Taking first word of name slot, {}, as name.'.format(name_slot, name))
            return UserIntent.yes, name

        # If no name slot, just try proper nouns
        proper_nouns = self.state_manager.current_state.corenlp['proper_nouns']
        if proper_nouns:
            name = proper_nouns[0]
            logger.primary_info('Didn\'t detect MyNameIsIntent. Have proper_nouns={}. Using first one, {}, as name'.format(proper_nouns, name))
            return UserIntent.yes, proper_nouns[0]

        # Otherwise, if the user only said one word, and it's not a high-frequency unigram, assume that's the name
        stripped_user_utterance = user_utterance.split()
        for yes_word in YES:
            if yes_word in stripped_user_utterance:
                stripped_user_utterance.remove(yes_word)
        stripped_user_utterance = " ".join(stripped_user_utterance)
        if self.could_be_name(stripped_user_utterance):
            logger.primary_info('Didn\'t detect MyNameIsIntent, but utterance is length 1 and is not a high-frequency unigram, so assuming name={}'.format(stripped_user_utterance))
            return UserIntent.yes, stripped_user_utterance

        # Otherwise if the user just said yes, set user intent accordingly
        if user_utterance in YES:
            logger.primary_info("Detected that user only said yes.")
            return UserIntent.yes_without_name, None

        return UserIntent.yes, None

    def get_response(self, state: State) -> ResponseGeneratorResult:

        # Try to get name from utterance
        utterance = self.state_manager.current_state.text
        user_intent, user_name = self.get_name_from_utterance(utterance)  # str or None
        logger.primary_info(f"Detected UserIntent {user_intent}.")
        if user_name is not None and contains_offensive(user_name, 'User name "{}" contains offensive phrase "{}", so acting like we didn\'t detect name.'):
            user_name = None

        if user_intent == UserIntent.yes or user_intent == UserIntent.yes_without_name:
            # If we got the name, save it and say intro phrase
            if user_name:
                setattr(self.state_manager.user_attributes, 'name', user_name)
                return ResponseGeneratorResult(text=random.choice(GREET_WITH_NAME).format(user_name),
                                               priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                               state=state, cur_entity=None,
                                               smooth_handoff=SmoothHandoff.LAUNCH_TO_NEURALCHAT,
                                               conditional_state=ConditionalState(None,
                                                                                  user_intent=user_intent))

            # If we didn't get the name and we have not asked before, ask for name
            elif state.asked_name_counter == 0 or user_intent == UserIntent.yes_without_name:
                logger.primary_info('Was unable to detect name, but have not asked for name, so asking for name again')
                return ResponseGeneratorResult(text=ASK_NAME_FIRST_TIME, priority=ResponsePriority.STRONG_CONTINUE,
                                               needs_prompt=False, state=state, cur_entity=None,
                                               conditional_state=ConditionalState(HandleNameTreelet.__name__,
                                                                                  user_intent=user_intent))

            # If we didn't get the name and we've asked once before, ask again
            elif state.asked_name_counter == 1:
                logger.primary_info('Was unable to detect name, so asking for name again')
                return ResponseGeneratorResult(text=ASK_NAME_AGAIN, priority=ResponsePriority.STRONG_CONTINUE,
                                               needs_prompt=False, state=state, cur_entity=None,
                                               conditional_state=ConditionalState(HandleNameTreelet.__name__,
                                                                                  user_intent=user_intent))

            # If we didn't get the name but we've already asked too many times, greet without name and move on
            else:
                return ResponseGeneratorResult(text=random.choice(GREET_WITHOUT_NAME), priority=ResponsePriority.STRONG_CONTINUE,
                                               needs_prompt=True, state=state, cur_entity=None,
                                               smooth_handoff=SmoothHandoff.LAUNCH_TO_NEURALCHAT,
                                               conditional_state=ConditionalState(None,
                                                                                  user_intent=user_intent))
        elif user_intent == UserIntent.no:
            return ResponseGeneratorResult(text=MOVING_ON, priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                           state=state, cur_entity=None,
                                           smooth_handoff=SmoothHandoff.LAUNCH_TO_NEURALCHAT,
                                           conditional_state=ConditionalState(None, user_intent=user_intent))

        elif user_intent == UserIntent.why:
            return ResponseGeneratorResult(text="Oh, I just want to get to know you! But if you'd prefer to stay "
                                                "anonymous, that's no problem. So, do you mind telling me your "
                                                "name?", priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                                           state=state, cur_entity=None,
                                           conditional_state=ConditionalState(HandleNameTreelet.__name__,
                                                                              user_intent=user_intent))

        elif user_intent == UserIntent.repeat:
            return ResponseGeneratorResult(text="Ok! What's your name?", priority=ResponsePriority.STRONG_CONTINUE,
                                           needs_prompt=False, state=state, cur_entity=None,
                                           conditional_state=ConditionalState(HandleNameTreelet.__name__,
                                                                              user_intent=user_intent))

        # If we didn't get the name but we've already asked too many times, greet without name with needs_prompt=True,
        # and smooth handoff to the next part of the launch sequence
        else:
            return ResponseGeneratorResult(text=random.choice(GREET_WITHOUT_NAME), priority=ResponsePriority.STRONG_CONTINUE,
                                           needs_prompt=True, state=state, cur_entity=None,
                                           smooth_handoff=SmoothHandoff.LAUNCH_TO_NEURALCHAT,
                                           conditional_state=ConditionalState(None))

    def get_prompt(self, state: State) -> PromptResult:
        return emptyPrompt(state)