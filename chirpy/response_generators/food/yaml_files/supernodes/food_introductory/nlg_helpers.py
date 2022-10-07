from chirpy.core.response_generator import nlg_helper
from chirpy.response_generators.food.yaml_files.supernodes.nlg_supernode_helper import *

import random

@nlg_helper
def sample_food_containing_ingredient(rg, food):
    food = food.lower()
    return random.choice([item for item, item_data in FOODS.items() if ('ingredients' in item_data and food in item_data['ingredients'])])

@nlg_helper 
def get_best_attribute_value(rg, food):
    food_data = get_food_data(food)
    if 'ingredients' in food_data:
        return sample_ingredient(food)
    elif 'texture' in food_data:
        return food_data['texture']

# TODO: Future Work
# CUSTOM_STATEMENTS = {
#     'chocolate': "I especially love how rich and smooth it is."
# }
#
# @nlg_helper
# def get_custom_comment(rg, cur_food):
#     return CUSTOM_STATEMENTS.get(cur_food, None)



