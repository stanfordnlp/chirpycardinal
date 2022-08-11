from chirpy.core.response_generator import nlg_helper
from chirpy.response_generators.food.yaml_files.supernodes.nlg_supernode_helper import *

from chirpy.core.response_priority import PromptType
from chirpy.core.response_generator_datatypes import PromptResult, AnswerType
from chirpy.response_generators.food.state import State, ConditionalState

@nlg_helper
def get_prompt_for_open_ended(rg, conditional_state=None):
    state, utterance, response_types = rg.get_state_utterance_response_types()

    if conditional_state and conditional_state.cur_food_entity:
        cur_food_entity = conditional_state.cur_food_entity
    else:
        cur_food_entity = state.cur_food_entity
        if conditional_state:
            conditional_state = ConditionalState(cur_food_entity=cur_food_entity,
                                                 prompt_treelet=conditional_state.prompt_treelet)
        else:
            conditional_state = ConditionalState(cur_food_entity=cur_food_entity)

    if cur_food_entity is None: return rg.emptyPrompt()

    best_attribute, best_attribute_value = get_attribute(cur_food_entity.name)
    pronoun = infl('them', cur_food_entity.is_plural)
    if best_attribute: text = 'What do you think?'
    else: text = f'What do you like best about {pronoun}?'

    return PromptResult(text, PromptType.CONTEXTUAL, state=state,
                        cur_entity=cur_food_entity, conditional_state=conditional_state)
