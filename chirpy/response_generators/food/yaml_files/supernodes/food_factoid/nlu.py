from chirpy.core.response_generator.response_type import ResponseType

def nlu_processing(rg, state, utterance, response_types):
    flags = {
        'thats': False,
        'didnt_know': False,
    }
    if ResponseType.THATS in response_types:
        flags['thats'] = True
    elif ResponseType.DIDNT_KNOW in response_types:
        flags['didnt_know'] = True
    return flags
