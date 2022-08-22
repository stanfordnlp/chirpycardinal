from chirpy.response_generators.food.yaml_files.supernodes.nlg_supernode_helper import *

from chirpy.core.response_generator.response_type import ResponseType

def response_nlu_processing(rg, state, utterance, response_types):
    response_flags = {
        'user_asked_q': False,
        'user_made_statement': False,
        'factoid_exists': False
    }
    cur_food_entity = state.cur_food_entity

    if ResponseType.QUESTION in response_types or len(utterance.split()) < 2:
        response_flags['user_asked_q'] = True
    else:
        response_flags['user_made_statement'] = True

    if get_factoid(cur_food_entity) is not None:
        response_flags['factoid_exists'] = True
    return response_flags


def prompt_nlu_processing(rg, conditional_state):
    prompt_flags = {
        'no_cur_food_entity': False,
        'has_best_attribute': False,
    }
    cur_food_entity = conditional_state.cur_food_entity
    cur_food = cur_food_entity.name.lower()

    if cur_food_entity:
        prompt_flags['exists_cur_food_entity'] = True

    best_attribute, best_attribute_value = get_attribute(cur_food)
    if best_attribute:
        prompt_flags['has_best_attribute'] = True
    return prompt_flags