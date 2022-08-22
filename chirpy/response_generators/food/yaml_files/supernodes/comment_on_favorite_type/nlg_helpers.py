from chirpy.core.response_generator import nlg_helper
from chirpy.response_generators.food.yaml_files.supernodes.nlg_supernode_helper import *


import random
from chirpy.core.response_priority import PromptType
from chirpy.core.response_generator_datatypes import AnswerType, PromptResult
from chirpy.response_generators.food.state import State, ConditionalState

@nlg_helper
def get_custom_question(rg, cur_food):
    cur_food = cur_food.lower()
    if cur_food in CUSTOM_QUESTIONS:
        return CUSTOM_QUESTIONS[cur_food][0]
    return None

@nlg_helper
def get_neural_response_food_type(rg):
    state, utterance, response_types = rg.get_state_utterance_response_types()
    user_answer, is_plural = get_best_candidate_user_entity(rg, utterance, state.cur_food_entity.name)
    copula = infl('are', is_plural)
    pronoun = infl('they', is_plural)
    prefix = f'{user_answer} {copula} a great choice! I especially love how {pronoun}'
    resp = rg.get_neural_response(prefix=prefix)
    resp = resp.replace('!', '.').split('.')[0] + '.' # only take one sentence
    return resp

RESTAURANTS = {
    "mcdonald's": ["Big Mac", "Filet-o-Fish"],
    "burger king": ["Whopper", "Double Whopper"],
    "subway": ["Footlong"],
    "popeye's": ["Popeye Chicken Sandwich"],
    "olive garden": ["breadstick"]
}

@nlg_helper
def get_custom_question_answer(rg, cur_food):
    cur_food = cur_food.lower()
    if cur_food in CUSTOM_QUESTIONS:
        return CUSTOM_QUESTIONS[cur_food][1]
    elif cur_food in RESTAURANTS:
        return random.choice(RESTAURANTS[cur_food])
    return None

@nlg_helper
def get_user_answer(rg, cur_food):
    state, utterance, response_types = rg.get_state_utterance_response_types()
    user_answer, is_plural = get_best_candidate_user_entity(rg, utterance, cur_food)
    return user_answer

@nlg_helper
def sample_from_type(rg, food):
    food = food.lower()
    foods = [(f, f_data) for f, f_data in FOODS.items() if f_data['type'] == food]
    weights = [f_data['views']**2 for f, f_data in foods]
    food_name, food_data = random.choices(foods, weights=weights)[0]
    return food_name
