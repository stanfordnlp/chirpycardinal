import re
import logging
from typing import Optional

from chirpy.core.callables import RemoteCallable, ResponseGenerator, get_url
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import emptyResult, ResponseGeneratorResult, PromptResult, emptyPrompt, \
    UpdateEntity

logger = logging.getLogger('chirpylogger')

DEFLECTION_RESPONSE = 'Sorry, I\'m unable to offer {} advice.'
DONT_KNOW_RESPONSE = 'Sorry, I don\'t know much about {} so I cannot answer that.'

IDENTITY_QUESTIONS = [
    ((r'[\w\s\']*your name[\w\s]*', r'[\w\s\']*you called[\w\s]*'),  'Sorry, I have to remain anonymous for this competition.'),
    ((r'[\w\s\']*who are you$', r'[\w\s\']*what are you$'), 'I am an Alexa Prize social bot built by a university.'),
    ((r'[\w\s\']*where[\w\s\']*you[\w\s]*live', r'[\w\s\']*where[\w\s\']*you[\w\s\']*from', r'[\w\s\']*where are you( |$)[\w\s\']*'), 'I live in the cloud. It\'s quite comfortable since it\'s so soft.')
]

def get_identity_deflection_response(text):
    if not text:
        return None
    for question in IDENTITY_QUESTIONS:
        if any(re.match(q, text) for q in question[0]):
            return question[1]
    return None


def utterance_contains_word(utterance, word):
    """
    Returns True iff utterance contains word surrounded by either spaces or apostrophes.

    i.e. if word="siri", then
    utterance="do you like siri" -> True
    utterance="do you like siri's voice" -> True
    utterance="I like the greek god osiris" -> False
    """
    tokens = re.split(" |'", utterance)  # split by space or apostrophe
    return word in tokens


class RedQuestionResponseGenerator(ResponseGenerator):
    name='RED_QUESTION'

    def init_state(self) -> dict:
        return {}

    def get_entity(self, state) -> UpdateEntity:
        return UpdateEntity(False)

    def advice_type(self, text):
        """
        Determine whether user's utterance text is asking for legal/medical/financial advice.
        Returns: str. Either 'legal', 'medical', 'financial', or None
        """
        # <=3 word utterances are not asking for advice (bold assumption!)
        if len(text.split(' ')) <= 3:
            return None

        # Run classifier for legal/financial/medical questions
        rqdetector = RemoteCallable(url=get_url("redquestiondetector"),
                                  timeout=1)
        rqdetector.name = 'redquestion'
        response = rqdetector({'text': text}) 
        if not response:
            return response

        # Deal with any other errors
        if ('error' in response and response['error']) or 'response' not in response:
            logger.error('Error when running RedQuestion Response Generator: {}'.format(response))
            return None

        # If we detected a red advice question, return the type
        if response['response'] in ['financial', 'medical', 'legal'] and response['response_prob'] > 0.75:
            return response['response']

        return None


    def get_response(self, state: dict) -> ResponseGeneratorResult:
        text = self.state_manager.current_state.text

        if text == '':  # e.g. on first turn
            return emptyResult(state)

        # If text mentions siri or cortana, say don't know
        for virtual_assistant in ['siri', 'cortana']:
            if utterance_contains_word(text, virtual_assistant):
                return ResponseGeneratorResult(text=DONT_KNOW_RESPONSE.format(virtual_assistant),
                                               priority=ResponsePriority.FORCE_START, needs_prompt=True, state=state,
                                               cur_entity=None)

        # If text is asking an identity question, deflect
        identity_response = get_identity_deflection_response(text)
        if identity_response:
            return ResponseGeneratorResult(text=identity_response, priority=ResponsePriority.FORCE_START,
                                           needs_prompt=True, state=state, cur_entity=None)

        # If text is asking a banned advice question, deflect
        advice_type = self.advice_type(text)
        if advice_type is not None:
            return ResponseGeneratorResult(text=DEFLECTION_RESPONSE.format(advice_type),
                                           priority=ResponsePriority.FORCE_START, needs_prompt=True, state=state,
                                           cur_entity=None)

        return emptyResult(state)


    def get_prompt(self, state: dict) -> PromptResult:
        return emptyPrompt(state)

    def update_state_if_chosen(self, state: dict, conditional_state: Optional[dict]) -> dict:
        return state

    def update_state_if_not_chosen(self, state: dict, conditional_state: Optional[dict]) -> dict:
        return state
