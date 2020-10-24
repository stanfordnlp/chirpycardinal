"""
This RG is for confirming if the user wants to exit.
"""
import random
import logging
from typing import Optional

from chirpy.core.callables import ResponseGenerator
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyPrompt, emptyResult, \
    UpdateEntity
from chirpy.core.regex.templates import ClosingNegativeConfirmationTemplate, ClosingPositiveConfirmationTemplate, TryingToStopTemplate

logger = logging.getLogger('chirpylogger')

CLOSING_CONFIRMATION_QUESTION = ['I\'m hearing that you want to end this conversation. Is that correct?',
                                 'If I\'m understanding correctly, you\'d like to end this conversation. Is that right?',
                                 'Are you saying that you\'d like to stop talking for now?']
CLOSING_CONFIRMATION_CONTINUE = ['Ok! I\'m happy you want to keep talking with me',
                                 'Great! I\'d like to keep talking to you, too',
                                 'Sounds good! Let\'s keep chatting',
                                 'I\'d love to talk some more!']

CLOSING_CONFIRMATION_STOP = 'Ok I will stop'
CLOSING_MEDIUM_CONFIDENCE_THRESHOLD = 0.85

class ClosingConfirmationResponseGenerator(ResponseGenerator):
    name='CLOSING_CONFIRMATION'
    """
    An RG that confirms if the user wants to exit the converation.
    """
    def init_state(self) -> dict:
        # init the state to remember if we have aksed if the user wants to exit
        return {
            'has_just_asked_to_exit': False,
        }

    def get_entity(self, state) -> UpdateEntity:
        return UpdateEntity(False)

    def user_trying_to_stop(self) -> bool:
        """Returns True iff the user seems to be trying to stop the conversation"""

        # Check P(closing) from the dialog act model
        dialog_act_output = self.state_manager.current_state.dialog_act
        if dialog_act_output is not None and dialog_act_output['probdist']['closing'] > CLOSING_MEDIUM_CONFIDENCE_THRESHOLD:
            logger.primary_info(f'P(closing intent)>{CLOSING_MEDIUM_CONFIDENCE_THRESHOLD} so user may be trying to stop the conversation')
            return True

        # Check the navigational intent
        nav_intent_output = self.state_manager.current_state.navigational_intent
        if nav_intent_output.neg_intent and nav_intent_output.neg_topic is None:
            logger.primary_info(f'User has negative navigational intent with neg_topic=None, so user may be trying to stop the conversation')
            return True
        
        # Check regex
        if TryingToStopTemplate().execute(self.state_manager.current_state.text) is not None:
            return True

        return False

    def get_response(self, state: dict) -> ResponseGeneratorResult:
        # If the user hasn't been asked whether they want to exit, look for closing intent
        if not state['has_just_asked_to_exit']:

            # If closing intent is detected, closing confirmation RG should respond
            if self.user_trying_to_stop():
                return ResponseGeneratorResult(text=random.choice(CLOSING_CONFIRMATION_QUESTION),
                                               priority=ResponsePriority.FORCE_START, needs_prompt=False, state=state,
                                               cur_entity=None, conditional_state={'has_just_asked_to_exit': True})
            else:
                return emptyResult(state)

        # If the user has been asked a confirmation question, handle their response
        else:

            # If the user wants to continue talking, request prompt and continue
            if self.state_manager.current_state.dialog_act['is_no_answer'] or \
                ClosingNegativeConfirmationTemplate().execute(self.state_manager.current_state.text) is not None:
                return ResponseGeneratorResult(text=random.choice(CLOSING_CONFIRMATION_CONTINUE),
                                               priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                               state=state, cur_entity=None,
                                               conditional_state={'has_just_asked_to_exit': False})

            # If the user wants to end the conversation, exit
            if self.state_manager.current_state.dialog_act['is_yes_answer'] or \
                ClosingPositiveConfirmationTemplate().execute(self.state_manager.current_state.text) is not None:
                return ResponseGeneratorResult(text=CLOSING_CONFIRMATION_STOP,
                                               priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                                               state=state, cur_entity=None,
                                               conditional_state={'has_just_asked_to_exit': False})

            # If neither matched, allow another RG to handle
            return emptyResult(state)

    def get_prompt(self, state: dict) -> PromptResult:
        return emptyPrompt(state)

    def update_state_if_chosen(self, state: dict, conditional_state: Optional[dict]) -> dict:
        return conditional_state

    def update_state_if_not_chosen(self, state: dict, conditional_state: Optional[dict]) -> dict:
        return {
            'has_just_asked_to_exit': False,
        }
