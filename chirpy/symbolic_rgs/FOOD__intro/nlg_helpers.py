#from chirpy.response_generators.food.food_helpers import get_intro_acknowledgement, sample_food_containing_ingredient, get_attribute
from chirpy.response_generators.food import food_helpers 
from chirpy.core.response_generator import nlg_helper, nlg_helper_augmented
import logging
import random

logger = logging.getLogger('chirpylogger')


INTRO_STATEMENTS = [
    "Ah yes, [FOOD] [copula] one of my favorite things to eat up here in the cloud.",
    "Oh yeah, [FOOD] [copula] such an amazing choice. It's one of my favorite foods up here in the cloud."
]

@nlg_helper 
def sample_food_containing_ingredient(rg, food: str):
    food = food.lower()
    logger.warning(f"Food is: {food}")
    logger.warning(f"{[item for item, item_data in food_helpers.FOODS.items() if ('ingredients' in item_data and food in item_data['ingredients'])]}")
    return random.choice([item for item, item_data in food_helpers.FOODS.items() if ('ingredients' in item_data and food in item_data['ingredients'])])




CUSTOM_STATEMENTS = {
    'chocolate': "I especially love how rich and smooth it is."
}

@nlg_helper
def get_custom_comment(rg, cur_food):
    return CUSTOM_STATEMENTS.get(cur_food, None)

