import logging
import random
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyPrompt, ResponsePriority
from chirpy.response_generators.launch.state import ConditionalState, State
from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.core.smooth_handoffs import SmoothHandoff
from chirpy.response_generators.launch.launch_helpers import *

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
    name = "launch_handle_name_treelet"

    def get_intent_and_name_from_utterance(self) -> Tuple[UserIntent, Optional[str]]:
        state, utterance, response_types = self.get_state_utterance_response_types()
        """Tries to get user's name from their utterance. Returns bool (if user wanted to give name) and the name (string) (or None)"""

        # Check if user explicitly said they did not want to tell us their name, or expressed a negative sentiment
        no_slots = DoesNotWantToSayNameTemplate().execute(utterance)
        if no_slots or ResponseType.NEGATIVE_USER_SENTIMENT in response_types:
            self.rg.reset_user_attributes()
            logger.primary_info('Detected that user did not want to say name. Moving onto HOWDY conversation.')
            return UserIntent.no, None

        # Check if user asked us to repeat
        if "what" in utterance or ResponseType.REQUEST_REPEAT in response_types:
            return UserIntent.repeat, None

        # Check if user asked us why we want to know their name
        if "why" in utterance:
            return UserIntent.why, None

        user_name = get_name_from_utterance(self.rg, utterance)
        if user_name is not None:
            return UserIntent.yes, user_name

        # Otherwise if the user just said yes, set user intent accordingly
        if utterance in YES:
            logger.primary_info("Detected that user only said yes.")
            return UserIntent.yes_without_name, None

        return UserIntent.yes, None

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        # Try to get name from utterance
        state, utterance, response_types = self.get_state_utterance_response_types()
        user_intent, user_name = self.get_intent_and_name_from_utterance()  # str or None
        logger.primary_info(f"Detected UserIntent {user_intent}.")
        if user_name is not None and contains_offensive(user_name, 'User name "{}" contains offensive phrase "{}", '
                                              'so acting like we didn\'t detect name.'):
            user_name = None

        logger.primary_info(f"Asked name counter is: {state.asked_name_counter}")
        if user_intent == UserIntent.yes or user_intent == UserIntent.yes_without_name:
            # If we got the name, save it and say intro phrase
            if user_name:
                self.rg.reset_user_attributes()
                self.rg.set_user_attribute('name', user_name)
                return ResponseGeneratorResult(text=random.choice(GREET_WITH_NAME).format(user_name),
                                               priority=priority, needs_prompt=True,
                                               state=state, cur_entity=None,
                                               smooth_handoff=SmoothHandoff.LAUNCH_TO_NEURALCHAT,
                                               conditional_state=ConditionalState(
                                                   prev_treelet_str=self.name,
                                                   next_treelet_str=None,
                                                   user_intent=user_intent)
                                               )

            # If we didn't get the name and we have not asked before, ask for name
            elif state.asked_name_counter == 1:
                if user_intent == UserIntent.yes_without_name:
                    logger.primary_info('Was unable to detect name, but have not asked for name, so asking for name again')
                    return ResponseGeneratorResult(text=ASK_NAME_FIRST_TIME, priority=priority,
                                                   needs_prompt=False, state=state, cur_entity=None,
                                                   conditional_state=
                                                   ConditionalState(
                                                       prev_treelet_str=self.name,
                                                       next_treelet_str=self.name,
                                                       user_intent=user_intent)
                                                   )
                else:
                # If we didn't get the name and we've asked once before, ask again
                    logger.primary_info('Was unable to detect name, so asking for name again')
                    return ResponseGeneratorResult(text=ASK_NAME_AGAIN, priority=priority,
                                                   needs_prompt=False, state=state, cur_entity=None,
                                                   conditional_state=
                                                   ConditionalState(
                                                       prev_treelet_str=self.name,
                                                       next_treelet_str=self.name,
                                                       user_intent=user_intent
                                                   ))
            elif state.asked_name_counter == 2:
                if user_intent == UserIntent.yes_without_name and self.rg.get_previous_bot_utterance() == ASK_NAME_FIRST_TIME:
                    return ResponseGeneratorResult(text=ASK_NAME_AGAIN, priority=priority,
                                                   needs_prompt=False, state=state, cur_entity=None,
                                                   conditional_state=
                                                   ConditionalState(
                                                       prev_treelet_str=self.name,
                                                       next_treelet_str=self.name,
                                                       user_intent=user_intent)
                                                   )
            # If we didn't get the name but we've already asked too many times, greet without name and move on
            else:
                self.rg.reset_user_attributes()
                return ResponseGeneratorResult(text=random.choice(GREET_WITHOUT_NAME), priority=priority,
                                               needs_prompt=True, state=state, cur_entity=None,
                                               smooth_handoff=SmoothHandoff.LAUNCH_TO_NEURALCHAT,
                                               conditional_state=ConditionalState(
                                                   prev_treelet_str=self.name,
                                                   next_treelet_str=None,
                                                   user_intent=user_intent)
                                               )
        elif user_intent == UserIntent.no:
            return ResponseGeneratorResult(text=MOVING_ON, priority=priority, needs_prompt=True,
                                           state=state, cur_entity=None,
                                           smooth_handoff=SmoothHandoff.LAUNCH_TO_NEURALCHAT,
                                           conditional_state=ConditionalState(
                                               prev_treelet_str=self.name,
                                               next_treelet_str=None,
                                               user_intent=user_intent)
                                           )

        elif user_intent == UserIntent.why:
            return ResponseGeneratorResult(text="Oh, I just want to get to know you! But if you'd prefer to stay "
                                                "anonymous, that's no problem. So, do you mind telling me your "
                                                "name?", priority=priority, needs_prompt=False,
                                           state=state, cur_entity=None,
                                           conditional_state=ConditionalState(
                                               prev_treelet_str=self.name,
                                               next_treelet_str=self.name,
                                               user_intent=user_intent))

        elif user_intent == UserIntent.repeat:
            return ResponseGeneratorResult(text="Ok! What's your name?", priority=priority,
                                           needs_prompt=False, state=state, cur_entity=None,
                                           conditional_state=ConditionalState(next_treelet_str=self.rg.handle_name_treelet.name,
                                                                              user_intent=user_intent))

        # If we didn't get the name but we've already asked too many times, greet without name with needs_prompt=True,
        # and smooth handoff to the next part of the launch sequence
        return ResponseGeneratorResult(text=random.choice(GREET_WITHOUT_NAME),
                                       priority=priority,
                                       needs_prompt=True, state=state, cur_entity=None,
                                       smooth_handoff=SmoothHandoff.LAUNCH_TO_NEURALCHAT,
                                       conditional_state=ConditionalState(
                                           prev_treelet_str=self.name,
                                           next_treelet_str=None)
                                       )
