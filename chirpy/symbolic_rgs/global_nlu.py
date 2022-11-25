from chirpy.core.response_generator.nlu import *

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


@nlu_processing
def get_flags(rg, state, utterance):
	pass