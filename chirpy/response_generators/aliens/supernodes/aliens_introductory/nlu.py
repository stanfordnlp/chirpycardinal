from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType

def nlu_processing(rg, state, utterance, response_types):
    flags = {
        'entering_aliens': True
    }

    return flags

def prompt_nlu_processing(rg, state, utterance, response_types):
    flags = {'already_discussed_aliens': False, 'discuss_aliens': False}
    discussed_aliens_in_prev_convo = rg.get_user_attribute('discussed_aliens', False)
    state = rg.state
    num_convo_turns = len(rg.get_conversation_history()) // 2
    if state.have_prompted or num_convo_turns <= 30 or discussed_aliens_in_prev_convo:
        flags['already_discussed_aliens'] = True
    else:
         flags['discuss_aliens'] = True