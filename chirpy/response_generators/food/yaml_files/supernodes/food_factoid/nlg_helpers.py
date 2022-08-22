from chirpy.core.response_generator import nlg_helper
from chirpy.response_generators.food.yaml_files.supernodes.nlg_supernode_helper import *

from chirpy.core.response_priority import PromptType
from chirpy.core.response_generator_datatypes import PromptResult, AnswerType
from chirpy.response_generators.food.state import State, ConditionalState

@nlg_helper
def get_place_origin_for_food(rg, cur_food):
    cur_food = cur_food.lower()
    cur_food_data = get_food_data(cur_food)
    return cur_food_data['origin']

@nlg_helper
def get_time_origin_for_food(rg, cur_food_entity):
    cur_food = cur_food_entity.name.lower()
    cur_talkable_food = cur_food_entity.talkable_name
    cur_food_data = get_food_data(cur_food)
    year, time_comment = get_time_comment(cur_food_data['year'], cur_talkable_food)
    return year

@nlg_helper
def get_time_comment_for_food(rg, cur_food_entity):
    cur_food = cur_food_entity.name.lower()
    cur_talkable_food = cur_food_entity.talkable_name
    cur_food_data = get_food_data(cur_food)
    year, time_comment = get_time_comment(cur_food_data['year'], cur_talkable_food)
    return time_comment