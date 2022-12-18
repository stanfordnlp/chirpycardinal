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

# def get_factoid_kind(rg, cur_entity):
#     talkable_food = cur_entity.talkable_name
#     food_data = food_helpers.get_food_data(food)

#     if 'year' in food_data and food_helpers.get_time_comment(food_data['year'], talkable_food) is not None:
#         if 'origin' in food_data:
#             logger.warning("FACTOID KIND is now origin_and_year")
#             return 'origin_and_year'
#         else:
#             logger.warning("FACTOID KIND is now year")
#             return 'year'
#     elif 'origin' in food_data:
#         logger.warning("FACTOID KIND is now origin")
#         return 'origin'
#     return None

@nlg_helper
def get_food_origin(rg, food): 
    if not food_helpers.is_known_food(food):
        return None
    food_data = food_helpers.get_food_data(food)
    logger.warning(f"FACTOID includes ORIGIN: {'origin' in food_data}")
    if 'origin' in food_data:
        return food_data['origin']
    return None

YEAR_ENDINGS = ['st', 'th', 'nd', 'rd', ' century', 'BC']

@nlg_helper
def get_food_year(rg, food):
    if not food_helpers.is_known_food(food):
        return None
    food_data = food_helpers.get_food_data(food)
    
    if 'year' not in food_data:
        return None
    
    year = food_data['year'].strip()

    # the 4th century BC
    if 'century' in year or ' BC' in year: 
        if 'the' not in year: year = "the " + year
        return year
    
    year = year.strip()
    if year.endswith('s'):
        intyear = int(year[:-1])
    else:
        intyear = int(year)
    if intyear > 1800:
        return None
        
    return year

@nlg_helper
def get_food_ingredient(rg, food: str):
    return food_helpers.sample_ingredient(food)

@nlg_helper
def get_food_texture(rg, food: str):
    return food_helpers.get_texture(food)

@nlg_helper
def get_food_ingredient_of(rg, food: str):
    return food_helpers.sample_food_containing_ingredient(food)


CUSTOM_STATEMENTS = {
    'chocolate': "I especially love how rich and smooth it is."
}

@nlg_helper
def get_custom_comment(rg, cur_food):
    return CUSTOM_STATEMENTS.get(cur_food, None)

