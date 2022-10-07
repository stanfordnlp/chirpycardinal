from chirpy.core.response_generator.response_type import ResponseType
from chirpy.response_generators.food.yaml_files.supernodes.nlg_supernode_helper import *

def response_nlu_processing(rg, state, utterance, response_types):
    response_flags = {
        'thats': False,
        'didnt_know': False,
    }
    if ResponseType.THATS in response_types:
        response_flags['thats'] = True
    elif ResponseType.DIDNT_KNOW in response_types:
        response_flags['didnt_know'] = True
    return response_flags

def prompt_nlu_processing(rg, conditional_state):
    prompt_flags = {
        'is_known_food': False,
        'has_known_time_origin': False,
        'has_known_place_origin': False
    }
    cur_food_entity = conditional_state.cur_food_entity
    cur_food = cur_food_entity.name.lower()
    cur_talkable_food = cur_food_entity.talkable_name

    if cur_food in FOODS:
        prompt_flags['is_known_food'] = True

    cur_food_data = get_food_data(cur_food)
    if 'year' in cur_food_data and get_time_comment(cur_food_data['year'], cur_talkable_food) is not None:
        prompt_flags['has_known_time_origin'] = True
    if 'origin' in cur_food_data:
        prompt_flags['has_known_place_origin'] = True

    return prompt_flags


