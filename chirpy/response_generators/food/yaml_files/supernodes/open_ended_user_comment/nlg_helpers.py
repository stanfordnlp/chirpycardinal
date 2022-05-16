from chirpy.response_generators.food.state import State, ConditionalState
from chirpy.response_generators.food.food_helpers import *
from chirpy.core.response_priority import PromptType
from chirpy.core.response_generator import nlg_helper
from chirpy.core.response_generator_datatypes import PromptResult, AnswerType
from chirpy.core.util import infl

@nlg_helper
def get_prompt_for_open_ended(rg, conditional_state=None):
    state, utterance, response_types = rg.get_state_utterance_response_types()
    entity = rg.get_current_entity()
    
    if conditional_state and conditional_state.cur_food:
            entity = conditional_state.cur_food
    else:
        entity = state.cur_food
        conditional_state = ConditionalState(cur_food=entity)

    if entity is None: return rg.emptyPrompt()

    best_attribute, best_attribute_value = get_attribute(entity.name)
    pronoun = infl('them', entity.is_plural)
    if best_attribute: text = 'What do you think?'
    else: text = f'What do you like best about {pronoun}?'
    return PromptResult(text, PromptType.CONTEXTUAL, state=state, cur_entity=entity, conditional_state=conditional_state)
