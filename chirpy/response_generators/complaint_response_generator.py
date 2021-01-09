"""
This RG is for handling user complaints.
"""
import random
import logging
from typing import Optional

from chirpy.core.callables import ResponseGenerator
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyPrompt, emptyResult
from chirpy.core.regex.templates import CriticismTemplate, ComplaintClarificationTemplate, ComplaintMisheardTemplate, ComplaintRepetitionTemplate, ComplaintPrivacyTemplate

logger = logging.getLogger('chirpylogger')

COMPLAINT_THRESHOLD = 0.91

GENERIC_COMPLAINT_RESPONSE = [
    "Oops, it sounds like I didn't get that quite right! Let's talk about something else."
]

MISHEARD_COMPLAINT_RESPONSE = [
    "Elephants can pick up sound through their feet, ears, and trunks. But I just have a microphone! Sorry for the misunderstanding. Let's talk about something else.",
    "Dolphins can hear sounds from up to 15 miles away, but I can’t even hear you when we're this close. Sorry for the misunderstanding. Let's talk about something else."
]

CLARIFICATION_COMPLAINT_RESPONSE = [
    "Oh no, I think I wasn't clear. Let's talk about something else",
    "It sounds like I wasn't clear! Can we move onto something else?"
]

REPETITION_COMPLAINT_RESPONSE = [
    "I might be a chatbot, but right now I sound like a broken record! Let's talk about something new.",
    "Oops I said it again! Sorry for the repetition. Why don't we talk about something else?"
]

PRIVACY_COMPLAINT_RESPONSE = [
    "No worries, we don't have to talk about that. Let's move on to something else",
    "That's alright, we can talk about something else."
]

class ComplaintResponseGenerator(ResponseGenerator):
    name='COMPLAINT'
    """
    An RG that provides a polite deflection to offensive (abusive/rude/crude/controversial) user utterances
    """
    def init_state(self) -> dict:
        return {}

    def get_response(self, state: dict) -> ResponseGeneratorResult:
        utterance = self.state_manager.current_state.text
        
        response_text = None
        priority = ResponsePriority.NO
        
        if ComplaintMisheardTemplate().execute(utterance) is not None:
            logger.primary_info(f'User\'s utterance "{utterance}" matches matches misheard template. Responding with MISHEARD_COMPLAINT_RESPONSE')
            priority = ResponsePriority.FORCE_START
            response_text = self.state_manager.current_state.choose_least_repetitive(MISHEARD_COMPLAINT_RESPONSE)

        elif ComplaintClarificationTemplate().execute(utterance) is not None and not (self.state_manager.last_state_active_rg == 'WIKI'):
            logger.primary_info(f'User\'s utterance "{utterance}" matches matches clarificaton template. Responding with CLARIFICATION_COMPLAINT_RESPONSE')
            priority = ResponsePriority.FORCE_START
            response_text = self.state_manager.current_state.choose_least_repetitive(CLARIFICATION_COMPLAINT_RESPONSE)

        # Sometimes when doing convpara in wiki, they ask a "surprised/doubtful" what which is handled there
        elif ComplaintRepetitionTemplate().execute(utterance) is not None:
            logger.primary_info(f'User\'s utterance "{utterance}" matches matches repetition template. Responding with REPETITION_COMPLAINT_RESPONSE')
            priority = ResponsePriority.FORCE_START
            response_text = self.state_manager.current_state.choose_least_repetitive(REPETITION_COMPLAINT_RESPONSE)

        elif ComplaintPrivacyTemplate().execute(utterance) is not None:
            logger.primary_info(f'User\'s utterance "{utterance}" matches matches privacy template. Responding with PRIVACY_COMPLAINT_RESPONSE')
            priority = ResponsePriority.FORCE_START
            response_text = self.state_manager.current_state.choose_least_repetitive(PRIVACY_COMPLAINT_RESPONSE)
        
        elif self.state_manager.current_state.dialog_act['probdist']['complaint'] > COMPLAINT_THRESHOLD:
            logger.primary_info(f'User\'s utterance "{utterance}" matches was classified as a complaint. Responding with GENERIC_COMPLAINT_RESPONSE')
            priority = ResponsePriority.FORCE_START
            response_text = self.state_manager.current_state.choose_least_repetitive(GENERIC_COMPLAINT_RESPONSE)
            
        return ResponseGeneratorResult(text=response_text, priority=priority,
                                           needs_prompt=True, state=state, cur_entity=None)
        
    def get_prompt(self, state: dict) -> PromptResult:
        return emptyPrompt(state)

    def update_state_if_chosen(self, state: dict, conditional_state: Optional[dict]) -> dict:
        return state

    def update_state_if_not_chosen(self, state: dict, conditional_state: Optional[dict]) -> dict:
        return state

