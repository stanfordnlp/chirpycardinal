import logging
from typing import Set
from chirpy.core.response_generator import ResponseGenerator
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult
from chirpy.response_generators.red_question.red_question_helpers import *
from chirpy.response_generators.red_question.regex_templates import AreYouRecordingTemplate

logger = logging.getLogger('chirpylogger')


ID_WORDS = [
'voting identification number',
'passport number',
'national identity number',
'driver\'s license number',
'genetic test result',
'insee code',
'health insurance number',
'voter identification number',
'national insurance number',
'nhi number',
'vehicle registration plate number',
'national id number',
'business identification number',
'fiscal code',
'aadhaar number',
'permanent account number',
'national identity document',
'pension insurance number',
'unique population registry code',
'pan number',
'kreditkartennummer',
'identity card number',
'national health index number',
'social security number',
'european health insurance card',
'ssn',
'debitkartennummer',
'tax identification number',
'dl number',
'tax file number',
'aadhar card number',
'credit card number',
'health insurance card number',
'debit card number',
'national health service number',
'social insurance number',
'voter id number',
'nie number',
'medical card number',
'driving license number',
'national health insurance number',
'vehicle registration number',
'business id number',
'pan card number',
'office id card number',
'tds number',
'pin number',
'account password',
'credit card',
'debit card',
'personal account',
'bank account',
'savings account',
'salary account'
]


class RedQuestionResponseGenerator(ResponseGenerator):
    name='RED_QUESTION'

    def __init__(self, state_manager):
        super().__init__(state_manager, can_give_prompts=False)

    def manual_deflect(self, text):
        for prompt, response in MANUAL_DEFLECTION.items():
            if re.match(prompt, text): return response
        return None

    def identify_response_types(self, utterance) -> Set[ResponseType]:
        response_types = super().identify_response_types(utterance)

        for virtual_assistant in ['siri', 'cortana']:
            if utterance_contains_word(utterance, virtual_assistant):
                response_types.add(ResponseType.VIRTUAL_ASSISTANT)

        if get_identity_deflection_response(utterance) is not None:
            response_types.add(ResponseType.ASKS_IDENTITY)

        advice_type_ = advice_type(utterance) or self.manual_deflect(utterance)
        if advice_type_ is not None:
            response_types.add(ResponseType.REQUEST_ADVICE)

        if AreYouRecordingTemplate().execute(utterance) is not None:
            response_types.add(ResponseType.ASKS_RECORDING)

        return response_types

    def handle_default_post_checks(self):
        state, utterance, response_types = self.get_state_utterance_response_types()
        if utterance == '':  # e.g. on first turn
            return self.emptyResult()

        # If text mentions siri or cortana, say don't know
        for virtual_assistant in ['siri', 'cortana']:
            if utterance_contains_word(utterance, virtual_assistant):
                return ResponseGeneratorResult(text=DONT_KNOW_RESPONSE.format(virtual_assistant),
                                               priority=ResponsePriority.FORCE_START, needs_prompt=True, state=state,
                                               cur_entity=None)

        # If text is asking an identity question, deflect
        if ResponseType.ASKS_IDENTITY in response_types:
            return ResponseGeneratorResult(text=get_identity_deflection_response(utterance),
                                           priority=ResponsePriority.FORCE_START,
                                           needs_prompt=True, state=state, cur_entity=None)

        # If text is asking a banned advice question, deflect
        if ResponseType.REQUEST_ADVICE in response_types:
            advice_type_ = advice_type(utterance) or self.manual_deflect(utterance)
            return ResponseGeneratorResult(text=DEFLECTION_RESPONSE.format(advice_type_),
                                           priority=ResponsePriority.FORCE_START, needs_prompt=True, state=state,
                                           cur_entity=None)

        # If user asks if we record conversations
        if ResponseType.ASKS_RECORDING in response_types:
            return ResponseGeneratorResult(text=RECORD_RESPONSE, priority=ResponsePriority.FORCE_START,
                                           needs_prompt=True, state=state, cur_entity=None)

        if any(id_word in utterance for id_word in ID_WORDS):
            return ResponseGeneratorResult(text="Sorry, I can't talk about that.", priority=ResponsePriority.FORCE_START,
                                           needs_prompt=True, state=state, cur_entity=None)


        return self.emptyResult()
