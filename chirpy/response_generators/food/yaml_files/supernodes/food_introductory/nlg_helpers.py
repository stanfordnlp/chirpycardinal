#from chirpy.response_generators.food.food_helpers import get_intro_acknowledgement, sample_food_containing_ingredient, get_attribute
from chirpy.response_generators.food import food_helpers 
from chirpy.core.response_generator import nlg_helper, nlg_helper_augmented
from chirpy.core.util import infl

INTRO_STATEMENTS = [
    "Ah yes, [FOOD] [copula] one of my favorite things to eat up here in the cloud.",
    "Oh yeah, [FOOD] [copula] such an amazing choice. It's one of my favorite foods up here in the cloud."
]

@nlg_helper
def intro_response(rg):
    entity = rg.get_current_entity()
    cur_food = entity.talkable_name
    
    # if cur_food in food_helpers.RESTAURANTS:
    #     return f"I really love the food from {cur_food}!"
    cur_food = cur_food.lower()
    #if cur_food in CUSTOM_COMMENTS: return CUSTOM_COMMENTS[cur_food]

    #intro_statement = random.choice(INTRO_STATEMENTS)
    #copula = infl('is', is_plural)
    #return intro_statement.replace('[copula]', copula).replace('[FOOD]', cur_food)
    #intro = get_intro_acknowledgement(cur_talkable_food, entity.is_plural)
    #return intro

@nlg_helper 
def get_best_attribute_value(rg, food):
    food_data = food_helpers.get_food_data(food)
    if 'ingredients' in food_data:
        return sample_ingredient(food)
    elif 'texture' in food_data:
        return food_data['texture']

@nlg_helper
def texture_attribute(rg, cur_food):
    entity = rg.get_current_entity()
    pronoun = 'they' if entity.is_plural else 'it'
    copula = 'they\'re' if entity.is_plural else 'it\'s'
    best_attribute, best_attribute_value = get_attribute(cur_food)
    return f"Personally, I love {pronoun} texture, especially how {copula} so {best_attribute_value}."

@nlg_helper
def food_is_ingr_response(rg, cur_food):
    parent_food = sample_food_containing_ingredient(cur_food)
    entity = rg.get_current_entity()
    copula = 'they\'re' if entity.is_plural else 'it\'s'
    containment_response = f"In my opinion, I think {copula} especially good as a part of {engine.a(parent_food)}."
    return containment_response



CUSTOM_STATEMENTS = {
    'chocolate': "I especially love how rich and smooth it is."
}

@nlg_helper
def get_custom_comment(rg, cur_food):
    return CUSTOM_STATEMENTS.get(cur_food, None)

