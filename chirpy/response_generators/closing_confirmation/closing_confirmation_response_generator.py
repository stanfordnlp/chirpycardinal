"""
This RG is for confirming if the user wants to exit.
"""
import random
import logging
from typing import Optional

from chirpy.core.response_generator import ResponseGenerator
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator.response_type import ResponseType
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyPrompt, emptyResult, \
    UpdateEntity, AnswerType

from chirpy.core.regex.templates import ClosingNegativeConfirmationTemplate, ClosingPositiveConfirmationTemplate, TryingToStopTemplate
from chirpy.response_generators.closing_confirmation.state import *

logger = logging.getLogger('chirpylogger')

CLOSING_COMPLIMENTS = [
    "It's been so nice to talk to you, you're so easy to talk to.",
    "I've enjoyed our conversation, you're a wonderful conversationalist!",
    "It's been a pleasure to talk to you, you're a really great listener."
]

CLOSING_CONFIRMATION_QUESTION = ["I'm hearing that you want to end this conversation. Is that correct?",
                                 "If I'm understanding correctly, you'd like to end this conversation. Is that right?",
                                 "Are you saying that you'd like to stop talking for now?"]
CLOSING_CONFIRMATION_CONTINUE = ["Ok! I'm happy you want to keep talking with me",
                                 "Great! I'd like to keep talking to you, too",
                                 "Sounds good! Let's keep chatting",
                                 "I'd love to talk some more!"]

CLOSING_CONFIRMATION_STOP = 'Ok I will stop'
CLOSING_MEDIUM_CONFIDENCE_THRESHOLD = 0.85

class ClosingConfirmationResponseGenerator(ResponseGenerator):
    """
    An RG that confirms if the user wants to exit the conversation.
    """
    name='CLOSING_CONFIRMATION'
    def __init__(self, state_manager):
        super().__init__(state_manager, can_give_prompts=False, state_constructor=State,
                         conditional_state_constructor=ConditionalState)

    def user_trying_to_stop(self) -> bool:
        """Returns True iff the user seems to be trying to stop the conversation"""
        utt = self.utterance
        # Check P(closing) from the dialog act model
        dialogact_output = self.state_manager.current_state.dialogact
        if dialogact_output is not None and dialogact_output['probdist']['closing'] > \
                CLOSING_MEDIUM_CONFIDENCE_THRESHOLD and "about" not in utt: # prevent false positive: "can we stop talking about it"
            logger.primary_info(f'P(closing intent)>{CLOSING_MEDIUM_CONFIDENCE_THRESHOLD} so user may be trying to stop the conversation')
            return True

        # Check the navigational intent
        # nav_intent_output = self.get_navigational_intent_output()
        # if nav_intent_output.neg_intent and nav_intent_output.neg_topic is None:
        #     logger.primary_info(f'User has negative navigational intent with neg_topic=None, so user may be trying to stop the conversation')
        #     return True

        # Check regex
        if TryingToStopTemplate().execute(utt) is not None:
            logger.primary_info("Trying to stop template was triggered.")
            return True

        return False

    @staticmethod
    def get_closing_confirmation():
        return f"Alright, {random.choice(CLOSING_COMPLIMENTS)} {random.choice(CLOSING_CONFIRMATION_QUESTION)}"

    def handle_custom_activation_checks(self):
        state = self.get_current_rg_state()
        # If closing intent is detected, closing confirmation RG should respond
        if self.user_trying_to_stop():
            logger.primary_info("Detected user trying to stop")
            return ResponseGeneratorResult(text=self.get_closing_confirmation(),
                                           priority=ResponsePriority.FORCE_START, needs_prompt=False, state=state,
                                           cur_entity=None,
                                           conditional_state=ConditionalState(has_just_asked_to_exit=True), answer_type=AnswerType.QUESTION_SELFHANDLING)

    def handle_custom_continuation_checks(self):
        state, utterance, response_types = self.get_state_utterance_response_types()

        # If the user has been asked a confirmation question, handle their response
        if state.has_just_asked_to_exit:
            # If the user wants to end the conversation, exit
            if ResponseType.YES in response_types or \
                    ClosingPositiveConfirmationTemplate().execute(utterance) is not None:
                return ResponseGeneratorResult(text=CLOSING_CONFIRMATION_STOP,
                                               priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                                               state=state, cur_entity=None,
                                               conditional_state=ConditionalState(has_just_asked_to_exit=False))
            # If the user wants to continue talking, request prompt and continue
            if ResponseType.NO in response_types or \
                    ClosingNegativeConfirmationTemplate().execute(utterance) is not None:
                return ResponseGeneratorResult(text=random.choice(CLOSING_CONFIRMATION_CONTINUE),
                                               priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                               state=state, cur_entity=None,
                                               conditional_state=ConditionalState(has_just_asked_to_exit=False))
            # If neither matched, allow another RG to handle
            return self.emptyResult()

    def update_state_if_not_chosen(self, state: State, conditional_state: Optional[ConditionalState]) -> BaseState:
        state = super().update_state_if_not_chosen(state, conditional_state)
        state.has_just_asked_to_exit = False
        return state
