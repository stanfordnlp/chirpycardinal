from chirpy.response_generators.food.yaml_files.supernodes.nlg_supernode_helper import *

def nlu_processing(rg, state, utterance, response_types):
    flags = {'cur_food': None,
             'food_type_found': False,
             'no_food_entity_found': False}
    cur_food_entity = rg.get_current_entity()
    cur_food = cur_food_entity.name
    flags['cur_food'] = cur_food_entity     # TODO: (???) Might not need this -or- use it as local
    if get_custom_question(cur_food) or is_subclassable(cur_food):
        flags['food_type_found'] = True
    elif not is_known_food(cur_food):
        flags['no_food_entity_found'] = True
    else:
        flags['best_comment_type'] = get_best_attribute(cur_food)
    return flags

