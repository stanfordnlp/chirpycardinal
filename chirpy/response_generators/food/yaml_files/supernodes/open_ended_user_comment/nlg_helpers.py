from chirpy.response_generators.food.state import State, ConditionalState
from chirpy.core.response_priority import PromptType
from chirpy.core.response_generator import nlg_helper
from chirpy.core.response_generator_datatypes import PromptResult, AnswerType
from chirpy.core.util import infl
import chirpy.response_generators.food.food_helpers as food_helpers

import random

@nlg_helper
def get_prompt_for_open_ended(rg, conditional_state=None):
    state, utterance, response_types = rg.get_state_utterance_response_types()
    entity = rg.get_current_entity()
    
    if conditional_state and conditional_state.cur_food:
            entity = conditional_state.cur_food
    else:
        entity = state.cur_food
        if conditional_state:
            conditional_state = ConditionalState(cur_food=entity, prompt_treelet=conditional_state.prompt_treelet)
        else:
            conditional_state = ConditionalState(cur_food=entity)

    if entity is None: return rg.emptyPrompt()

    best_attribute, best_attribute_value = food_helpers.get_attribute(entity.name)
    pronoun = infl('them', entity.is_plural)
    if best_attribute: text = 'What do you think?'
    else: text = f'What do you like best about {pronoun}?'
    return PromptResult(text, PromptType.CONTEXTUAL, state=state, cur_entity=entity, conditional_state=conditional_state)

CONCLUDING_STATEMENTS = ["Anyway, I'm feeling hungry now! Thanks for recommending {}!",
                         "Anyway, thanks for talking to me about {}. I'll have to get some soon!"]

@nlg_helper
def get_concluding_statement(cur_food):
    return random.choice(CONCLUDING_STATEMENTS).format(cur_food)
