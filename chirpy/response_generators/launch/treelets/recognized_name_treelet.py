import logging
import random
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyPrompt, ResponsePriority
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.response_generators.launch.treelets import HandleNameTreelet
from chirpy.response_generators.launch.treelets.handle_name_treelet import MOVING_ON, ASK_NAME_AGAIN, \
    ASK_NAME_FIRST_TIME, GREET_WITHOUT_NAME, GREET_WITH_NAME
from chirpy.response_generators.launch.state import ConditionalState, State
from chirpy.response_generators.launch.launch_helpers import *
from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.regex.word_lists import YES, NO
from typing import Tuple, Optional
from chirpy.core.smooth_handoffs import SmoothHandoff

logger = logging.getLogger('chirpylogger')

GREET_RETURNING_USER = [
    "Great, it's nice to hear from you again, {}! You were so interesting the last time we talked.",
    "Cool, it's nice to talk to you again, {}! You made me laugh the last time we chatted.",
    "It's great to talk to you again today, {}. I enjoyed your company very much the last time we chatted.",
    "It's nice to be in a conversation with you again, {}. I really liked listening to you. "
]

class RecognizedNameTreelet(Treelet):
    def get_intent_and_name_from_utterance(self) -> Tuple[UserIntent, Optional[str]]:
        """
        Tries to get user's name from their utterance. Returns bool (if user wanted to give name)
        and the name (string) (or None)
        :return:
        """
        state, user_utterance, response_types = self.get_state_utterance_response_types()

        no_slots = DoesNotWantToSayNameTemplate().execute(user_utterance)
        extracted_name = get_name_from_utterance(self.rg, user_utterance, remove_no=True)

        # If user said no, and nothing else set user intent accordingly
        if user_utterance in NO:
            logger.primary_info("Detected that user only said no.")
            return UserIntent.no_without_name, None

        # Otherwise, if user said no and some other things, then check if they supplied a name
        if no_slots:
            logger.primary_info("Detected that user said no")
            if extracted_name is not None:
                logger.primary_info(f"User supplied another name: {extracted_name}")
                return UserIntent.no_with_name, extracted_name
            else:
                logger.primary_info(f"User did not supply a name correction")
                return UserIntent.no_without_name, None

        if ResponseType.YES in response_types:
            return UserIntent.yes, None

        if ResponseType.DISINTERESTED in response_types or ResponseType.NEGATIVE_USER_SENTIMENT in response_types:
            logger.primary_info("User has negative navigational intent / negative sentiment")
            return UserIntent.disinterested, None

        # Check if user asked us to repeat
        if "what" in user_utterance or ResponseType.REQUEST_REPEAT in response_types:
            return UserIntent.repeat, None

        # Check if user asked us why we want to know their name
        if "why" in user_utterance:
            return UserIntent.why, None

        if extracted_name is not None: # catches phrases without yes/no, such as "actually, i'm tommy"
            return UserIntent.no_with_name, extracted_name

        return UserIntent.yes, None

    def get_response(self, priority=ResponsePriority.FORCE_START, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()
        stored_name = self.rg.get_user_attribute('name', None)
        assert stored_name is not None # this treelet should only be used if a name is already available
        user_intent, user_name = self.get_intent_and_name_from_utterance()  # str or None

        logger.primary_info(f"Detected UserIntent {user_intent}.")
        if user_name is not None and contains_offensive(user_name, 'User name "{}" contains offensive phrase "{}", so acting like we didn\'t detect name.'):
            user_name = None

        if user_intent == UserIntent.disinterested:
            self.rg.reset_user_attributes()
            return ResponseGeneratorResult(text=MOVING_ON, priority=priority, needs_prompt=True,
                                           state=state, cur_entity=None,
                                           smooth_handoff=SmoothHandoff.LAUNCH_TO_NEURALCHAT,
                                           conditional_state=ConditionalState(
                                               prev_treelet_str=self.name,
                                               next_treelet_str=None,
                                               user_intent=user_intent)
                                           )

        elif user_intent == UserIntent.yes:
            turns_since_last_active = self.rg.get_user_attribute('turns_since_last_active', None)
            logger.primary_info(f"Recognized user, Turns since last active are: {turns_since_last_active}")

            if turns_since_last_active is not None and isinstance(turns_since_last_active, dict):
                setattr(self.get_current_state(), 'turns_since_last_active', turns_since_last_active)

            return ResponseGeneratorResult(text=random.choice(GREET_RETURNING_USER).format(stored_name),
                                           priority=priority, needs_prompt=True,
                                           state=state, cur_entity=None,
                                           smooth_handoff=SmoothHandoff.LAUNCH_TO_NEURALCHAT,
                                           conditional_state=ConditionalState(
                                               prev_treelet_str=self.name,
                                               next_treelet_str=None,
                                               user_intent=user_intent))

        elif user_intent == UserIntent.no_without_name:
            ASK_NAME_AFTER_WRONG = "Ah, my mistake. May I ask for your name?"
            self.rg.reset_user_attributes()
            return ResponseGeneratorResult(text=ASK_NAME_AFTER_WRONG, priority=ResponsePriority.FORCE_START,
                                           needs_prompt=False, state=state, cur_entity=None,
                                           conditional_state=ConditionalState(
                                               prev_treelet_str=self.name,
                                               next_treelet_str=self.rg.handle_name_treelet.name,
                                               user_intent=user_intent)
                                           )

        elif user_intent == UserIntent.no_with_name:
            prefix = "Ah, thank you for correcting me. "
            if user_name is not None:
                self.rg.reset_user_attributes()
                self.rg.set_user_attribute('name', user_name)
                return ResponseGeneratorResult(text=prefix + random.choice(GREET_WITH_NAME).format(user_name),
                                               priority=priority, needs_prompt=True,
                                               state=state, cur_entity=None,
                                               smooth_handoff=SmoothHandoff.LAUNCH_TO_NEURALCHAT,
                                               conditional_state=ConditionalState(
                                                   prev_treelet_str=self.name,
                                                   next_treelet_str=None,
                                                   user_intent=user_intent)
                                               )
            else:
                return ResponseGeneratorResult(text=prefix + random.choice(GREET_WITHOUT_NAME),
                                               priority=priority, needs_prompt=True,
                                               state=state, cur_entity=None,
                                               smooth_handoff=SmoothHandoff.LAUNCH_TO_NEURALCHAT,
                                               conditional_state=ConditionalState(
                                                   prev_treelet_str=self.name,
                                                   next_treelet_str=None,
                                                   user_intent=user_intent))

        elif user_intent == UserIntent.why:
            return ResponseGeneratorResult(text="Oh, I just want to get to know you! But if you'd prefer to stay "
                                                "anonymous, that's no problem. So, do you mind telling me your "
                                                "name?", priority=priority, needs_prompt=False,
                                           state=state, cur_entity=None,
                                           conditional_state=ConditionalState(
                                               prev_treelet_str=self.name,
                                               next_treelet_str=self.rg.handle_name_treelet.name,
                                               user_intent=user_intent))

        elif user_intent == UserIntent.repeat:
            return ResponseGeneratorResult(text="Ok! What's your name?", priority=priority,
                                           needs_prompt=False, state=state, cur_entity=None,
                                           conditional_state=ConditionalState(
                                               prev_treelet_str=self.name,
                                               next_treelet_str=self.rg.handle_name_treelet.name,
                                               user_intent=user_intent))

        # # If we didn't get the name but we've already asked too many times, greet without name with needs_prompt=True,
        # # and smooth handoff to the next part of the launch sequence
        # else:
        #     return ResponseGeneratorResult(text=random.choice(GREET_WITHOUT_NAME), priority=ResponsePriority.FORCE_START,
        #                                    needs_prompt=True, state=state, cur_entity=None,
        #                                    smooth_handoff=SmoothHandoff.LAUNCH_TO_NEURALCHAT,
        #                                    conditional_state=ConditionalState(None))
