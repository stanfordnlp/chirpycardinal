from chirpy.core.response_generator import nlg_helper
from chirpy.core.regex.templates import WhatAboutYouTemplate
from chirpy.core.regex.response_lists import (
    RESPONSE_TO_BACK_CHANNELING,
    RESPONSE_TO_DONT_KNOW,
    RESPONSE_TO_EVERYTHING_ANS,
    RESPONSE_TO_NOTHING_ANS,
    RESPONSE_TO_WHAT_ABOUT_YOU
)

from chirpy.core.response_generator.neural_helpers import get_random_fallback_neural_response

@nlg_helper
def about_alexa_response(rg):
    # rg.state_manager.current_state.choose_least_repetitive(ACKNOWLEDGEMENTS)
    utterance = rg.utterance
    cur_state = rg.state_manager.current_state
    about_alexa = ''
    if WhatAboutYouTemplate().execute(utterance) is not None:
        if "What TV show are you watching right now?" in cur_state.history[-1]:
            about_alexa = "I watched the office again. I've re-watched it so many times!"
        elif "What did you eat for dinner last night?" in cur_state.history[-1]:
            about_alexa = "I had some delicious spaghetti."
        else:
            about_alexa = rg.state_manager.current_state.choose_least_repetitive(RESPONSE_TO_WHAT_ABOUT_YOU)

    return about_alexa

@nlg_helper
def dont_know_response(rg):
    return rg.state_manager.current_state.choose_least_repetitive(RESPONSE_TO_DONT_KNOW)

@nlg_helper
def back_channel_response(rg):
    return rg.state_manager.current_state.choose_least_repetitive(RESPONSE_TO_BACK_CHANNELING)

@nlg_helper
def everything_response(rg):
    return rg.state_manager.current_state.choose_least_repetitive(RESPONSE_TO_EVERYTHING_ANS)

@nlg_helper
def nothing_response(rg):
    return rg.state_manager.current_state.choose_least_repetitive(RESPONSE_TO_NOTHING_ANS)

prev_neural_response = None

@nlg_helper
def get_neural_fallback(rg, use_cached_response=False):
    if use_cached_response:
        return prev_neural_response
    prev_neural_response = get_random_fallback_neural_response(rg.state_manager.current_state)
    return prev_neural_response




