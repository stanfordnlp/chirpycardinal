from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
from chirpy.core.response_generator import nlg_helper

@nlg_helper
def get_responses_to_thats():
    return RESPONSE_TO_THATS

@nlg_helper
def get_responses_to_didnt_know():
    return RESPONSE_TO_DIDNT_KNOW

@nlg_helper
def wish_I_could_play_instr(rg):
    entity = rg.get_instrument_entity()
    if entity is None:
        return f'Say, I really wish I can learn to play it one day. It seems like a great instrument.'
    else:
        return f'Say, I really wish I can learn to play the {entity.name} one day. It seems like a great instrument.'