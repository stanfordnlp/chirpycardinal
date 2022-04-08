from chirpy.response_generators.aliens.regex_templates import *
from chirpy.core.response_generator.response_type import add_response_types, ResponseType
import logging
logger = logging.getLogger('chirpylogger')

ADDITIONAL_RESPONSE_TYPES = ['OPINION']

ResponseType = add_response_types(ResponseType, ADDITIONAL_RESPONSE_TYPES)

def is_opinion(rg, utterance):
    top_da = rg.state_manager.current_state.dialogact['top_1']
    return len(utterance.split()) >= 10 or top_da == 'opinion'
