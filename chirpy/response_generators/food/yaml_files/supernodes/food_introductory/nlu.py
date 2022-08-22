from chirpy.response_generators.food.yaml_files.supernodes.nlg_supernode_helper import *

def response_nlu_processing(rg, state, utterance, response_types):
    response_flags = { 'food_type_found': False,
                        'no_food_entity_found': False,
                        'best_comment_type': False}
    cur_food_entity = rg.get_current_entity()
    cur_food = cur_food_entity.name
    if get_custom_question(cur_food) or is_subclassable(cur_food):
        response_flags['food_type_found'] = True
    elif not is_known_food(cur_food):
        response_flags['no_food_entity_found'] = True
    else:
        response_flags['best_comment_type'] = get_best_attribute(cur_food)
    return response_flags

