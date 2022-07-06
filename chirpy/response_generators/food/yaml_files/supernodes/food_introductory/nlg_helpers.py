from chirpy.response_generators.food.food_helpers import get_intro_acknowledgement, sample_food_containing_ingredient, get_attribute
from chirpy.core.response_generator import nlg_helper, nlg_helper_augmented

import inflect
engine = inflect.engine()

@nlg_helper_augmented
def intro_response():
    print("Inside eval, globals are", globals().keys())
    rg = globals()['rg']
    entity = rg.get_current_entity()
    cur_talkable_food = entity.talkable_name

    intro = get_intro_acknowledgement(cur_talkable_food, entity.is_plural)

    return intro

@nlg_helper
def ingredient_attribute(rg, cur_food):
    entity = rg.get_current_entity()
    pronoun = 'they' if entity.is_plural else 'it'
    best_attribute, best_attribute_value = get_attribute(cur_food)
    return f"Personally, I especially like the {best_attribute_value} in it, I think it gives {pronoun} a really nice flavor."

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

@nlg_helper
def get_pronoun(rg):
    entity = rg.get_current_entity()
    pronoun = 'they' if entity.is_plural else 'it'
    return pronoun

CUSTOM_STATEMENTS = {
    'chocolate': "I especially love how rich and smooth it is."
}

@nlg_helper
def get_custom_comment(cur_food):
    return CUSTOM_STATEMENTS.get(cur_food, None)

