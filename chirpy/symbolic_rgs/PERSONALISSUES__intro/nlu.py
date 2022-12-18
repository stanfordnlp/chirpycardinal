from chirpy.core.response_generator.nlu import nlu_processing

@nlu_processing
def get_flags(rg, state, utterance):
    pass

@nlu_processing
def get_background_flags(rg, utterance):
    return