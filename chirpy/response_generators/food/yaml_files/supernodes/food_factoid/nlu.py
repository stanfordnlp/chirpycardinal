from chirpy.response_generators.food.food_helpers import *

def nlu_processing(rg, state, utterance, response_types):
    flags = {
        'thats': False,
        'didnt_know': False,
        'agree_with_user': False
    }
    if ResponseType.THATS in response_types:
        flags['thats'] = True
    elif ResponseType.DIDNT_KNOW in response_types:
        flags['didnt_know'] = True
    else:
        flags['agree_with_user'] = True

    return flags
