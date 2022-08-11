from chirpy.response_generators.food.yaml_files.supernodes.nlg_supernode_helper import *
from chirpy.core.response_generator.response_type import ResponseType

def nlu_processing(rg, state, utterance, response_types):
	flags = {
		'has_custom_food': False,
		'dont_know': False,
		'response_no': False
	}
	cur_food_entity = state.cur_food_entity
	cur_food = cur_food_entity.name
	if get_custom_question(cur_food) is not None:
		flags['has_custom_food'] = True
		if ResponseType.DONT_KNOW in response_types:
			flags['dont_know'] = True
		elif ResponseType.NO in response_types:
			flags['response_no'] = True

	return flags
