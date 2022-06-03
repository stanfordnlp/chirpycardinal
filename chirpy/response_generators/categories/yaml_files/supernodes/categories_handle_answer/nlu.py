from chirpy.core.regex.templates import (
    DontKnowTemplate,
    BackChannelingTemplate,
    EverythingTemplate,
    NotThingTemplate,
    WhatAboutYouTemplate,
)

from chirpy.core.response_generator.response_type import ResponseType
from chirpy.response_generators.categories.yaml_files.supernodes.categories_handle_answer.nlg_helpers import get_neural_fallback

def nlu_processing(rg, state, utterance, response_types):
    flags = {
        'dont_know': False,
        'back_channeling': False,
        'everything_ans': False,
        'nothing_ans': False,
        'no_fallback': False
    }

    if ResponseType.DONT_KNOW in response_types:
        flags['dont_know'] = True
    elif BackChannelingTemplate().execute(utterance) is not None:
        flags['back_channeling'] = True
    elif EverythingTemplate().execute(utterance) is not None:
        flags['everything_ans'] = True
    elif NotThingTemplate().execute(utterance) is not None or ResponseType.NO in response_types:
        flags['nothing_ans'] = True
    else:
        text = get_neural_fallback(rg)
        if text is None:
            flags['no_fallback'] = True

    return flags