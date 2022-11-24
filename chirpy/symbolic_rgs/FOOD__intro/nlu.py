from chirpy.response_generators.food import food_helpers

def get_best_attribute(food):
    food_data = food_helpers.get_food_data(food)
    if 'ingredients' in food_data:
        return 'has_ingredient'
    elif 'texture' in food_data:
        return 'texture'
    elif food_helpers.is_ingredient(food):
        return 'is_ingredient'
    else:
        return None

def nlu_processing(rg, state, utterance, response_types):
    # flags = {
    #     'no_entity': False,
    #     'cur_food': None,
    #     'food_type_comment': False,
    #     'custom_comment_exists': False,
    #     'is_ingredient': False,
    #     'catch_all': False
    # }
    flags = {'cur_food': None, 'no_food_entity_found': False}
    entity = rg.get_current_entity()
    cur_food = entity.name.lower()
    flags['cur_food'] = cur_food
    cur_talkable_food = entity.talkable_name

    if not food_helpers.is_known_food(cur_food):
        flags['no_food_entity_found'] = True
        return flags 
        
    flags['best_comment_type'] = get_best_attribute(cur_food)        
    return flags

