from chirpy.core.response_generator.response_type import ResponseType

def nlu_processing(rg, state, utterance, response_types):
    flags = {
        'has_q': False
    }

    state_manager = rg.state_manager
    category_name = state.cur_category_name
    question = state.get_first_unasked_question(category_name, state_manager)

    if question:
        flags['has_q'] = True

    return flags

def prompt_nlu_processing(rg, state, utterance, response_types):
    flags = {
        'has_question': False
    }

    state_manager = rg.state_manager
    category_name = state.cur_category_name
    question = state.get_first_unasked_question(category_name)
    if question:
        flags['has_question'] = True


    return flags