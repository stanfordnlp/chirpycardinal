from chirpy.response_generators.food.state import State, ConditionalState
from chirpy.response_generators.food.food_helpers import *
from chirpy.core.response_priority import PromptType
from chirpy.core.response_generator_datatypes import PromptResult, AnswerType
from chirpy.core.util import infl
from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW

import random

def get_prompt_for_factoid(rg, conditional_state=None):
    state, utterance, response_types = rg.get_state_utterance_response_types()
	if conditional_state and conditional_state.cur_food:
        cur_food = conditional_state.cur_food
    else:
        cur_food = state.cur_food
        conditional_state = ConditionalState(cur_food=cur_food)

    entity = rg.state_manager.current_state.entity_tracker.cur_entity

    return PromptResult(text=get_factoid(cur_food), prompt_type=PromptType.CONTEXTUAL,
                        state=state, cur_entity=entity, conditional_state=conditional_state, answer_type=AnswerType.QUESTION_SELFHANDLING)

def get_thats_response():
    return random.choice(RESPONSE_TO_THATS)

def get_didnt_know_response():
    return random.choice(RESPONSE_TO_DIDNT_KNOW)

def get_neural_agreement(rg):
    return rg.get_neural_response(prefix=None, conditions=[lambda response: 'agree' in response])