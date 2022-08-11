from chirpy.response_generators.food.yaml_files.supernodes.nlg_supernode_helper import *

from chirpy.core.response_generator.response_type import ResponseType

def nlu_processing(rg, state, utterance, response_types):
    flags = {
        'user_asked_q': False,
        'user_made_statement': False,
        'factoid_exists': False
    }
    cur_food_entity = state.cur_food_entity
    # cur_food = cur_food_entity.name
    # cur_talkable_food = cur_food_entity.talkable_name

    if ResponseType.QUESTION in response_types or len(utterance.split()) < 2:
        flags['user_asked_q'] = True
    else:
        flags['user_made_statement'] = True

    if get_factoid(cur_food_entity) is not None:
        flags['factoid_exists'] = True
    return flags
