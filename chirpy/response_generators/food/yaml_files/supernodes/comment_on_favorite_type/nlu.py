from chirpy.response_generators.food.yaml_files.supernodes.nlg_supernode_helper import *
from chirpy.core.response_generator.response_type import ResponseType

def response_nlu_processing(rg, state, utterance, response_types):
	response_flags = {
		'has_custom_food': False,
		'dont_know': False,
		'response_no': False
	}
	cur_food_entity = state.cur_food_entity
	cur_food = cur_food_entity.name
	if get_custom_question(cur_food) is not None:
		response_flags['has_custom_food'] = True
		if ResponseType.DONT_KNOW in response_types:
			response_flags['dont_know'] = True
		elif ResponseType.NO in response_types:
			response_flags['response_no'] = True

	return response_flags

def prompt_nlu_processing(rg, conditional_state):
	prompt_flags = {
		'has_custom_food': False,
		'is_subclassable': False,
	}
	cur_food_entity = conditional_state.cur_food_entity
	custom_question = get_custom_question(cur_food_entity.name.lower())
	if custom_question is not None:
		prompt_flags['has_custom_food'] = True
	elif is_subclassable(cur_food_entity.name.lower()):
		prompt_flags['is_subclassable'] = True

	return prompt_flags
