from chirpy.response_generators.food.food_helpers import *

import inflect
engine = inflect.engine()

def intro_response(rg):
	entity = rg.get_current_entity()
	cur_talkable_food = entity.talkable_name

	intro = get_intro_acknowledgement(cur_talkable_food, entity.is_plural)

	return intro

def ingredient_attribute(rg, cur_food):
	entity = rg.get_current_entity()
	pronoun = 'they' if entity.is_plural else 'it'
	best_attribute, best_attribute_value = get_attribute(cur_food)
	return f"Personally, I especially like the {best_attribute_value} in it, I think it gives {pronoun} a really nice flavor."

def texture_attribute(rg, cur_food):
	entity = rg.get_current_entity()
	pronoun = 'they' if entity.is_plural else 'it'
	copula = 'they\'re' if entity.is_plural else 'it\'s'
	best_attribute, best_attribute_value = get_attribute(cur_food)
	return f"Personally, I love {pronoun} texture, especially how {copula} so {best_attribute_value}."

def food_is_ingr_response(rg, cur_food):
	parent_food = sample_food_containing_ingredient(cur_food)
	entity = rg.get_current_entity()
	copula = 'they\'re' if entity.is_plural else 'it\'s'
    containment_response = f"In my opinion, I think {copula} especially good as a part of {engine.a(parent_food)}."
    return containment_response

def get_pronoun(rg):
	entity = rg.get_current_entity()
	pronoun = 'they' if entity.is_plural else 'it'
	return pronoun