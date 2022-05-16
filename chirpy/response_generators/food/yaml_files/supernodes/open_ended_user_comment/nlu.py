from chirpy.response_generators.food.food_helpers import *

def nlu_processing(rg, state, utterance, response_types):
    flags = {
        'user_asked_q': False,
        'user_made_statement': False,
        'factoid_exists': False
    }
    entity = state.cur_food
    cur_food = entity.name
    cur_talkable_food = entity.talkable_name

    if ResponseType.QUESTION in response_types or len(utterance.split()) < 2:
        flags['user_asked_q'] = True
    else:
        flags['user_made_statement'] = True

    if get_factoid(entity) is not None:
        flags['factoid_exists'] = True

    return flags
