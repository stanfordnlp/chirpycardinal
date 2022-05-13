from chirpy.response_generators.food.food_helpers import *

def nlu_processing(rg, state, utterance, response_types):
	flags = {
		'no_entity': False,
		'cur_food': None,
		'food_type_comment': False,
		'custom_comment_exists': False,
		'best_attribute_ingredient': False,
		'best_attribute_texture': False,
		'is_ingredient': False,
		'catch_all': False
	}

	entity = rg.get_current_entity()
	if entity is None:
		flags['no_entity'] = True
		return flags

	cur_food = entity.name.lower()
	flags['cur_food'] = cur_food
    cur_talkable_food = entity.talkable_name

    if not is_known_food(cur_food):
    	flags['no_entity'] = True
    	return flags

    if get_custom_question(cur_food) or is_subclassable(cur_food):
    	flags['food_type_comment'] = True
    else:
    	best_attribute, best_attribute_value = get_attribute(cur_food)
        custom_comment = get_custom_comment(cur_food)
        if custom_comment is not None:
        	flags['custom_comment_exists'] = True
        elif best_attribute == 'ingredient':
        	flags['best_attribute_ingredient'] = True
        elif best_attribute == 'texture':
        	flags['best_attribute_texture'] = True
       	elif is_ingredient(cur_food):
       		flags['is_ingredient'] = True
       	else:
       		flags['catch_all'] = True

    return flags

