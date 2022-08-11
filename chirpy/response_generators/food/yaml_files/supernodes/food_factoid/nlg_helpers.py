from chirpy.core.response_generator import nlg_helper
from chirpy.response_generators.food.yaml_files.supernodes.nlg_supernode_helper import *

from chirpy.core.response_priority import PromptType
from chirpy.core.response_generator_datatypes import PromptResult, AnswerType
from chirpy.response_generators.food.state import State, ConditionalState

@nlg_helper
def get_prompt_for_factoid(rg, conditional_state=None):
    state, utterance, response_types = rg.get_state_utterance_response_types()
    if conditional_state and conditional_state.cur_food_entity:
        cur_food_entity = conditional_state.cur_food_entity
    else:
        cur_food_entity = state.cur_food_entity
        if conditional_state:
            conditional_state = ConditionalState(cur_food_entity=cur_food_entity,
                                                 cur_supernode=conditional_state.cur_supernode)
        else:
            conditional_state = ConditionalState(cur_food_entity=cur_food_entity)

    cur_entity = rg.state_manager.current_state.entity_tracker.cur_entity

    return PromptResult(text=get_factoid(cur_food_entity), prompt_type=PromptType.CONTEXTUAL,
                        state=state, cur_entity=cur_entity, conditional_state=conditional_state,
                        answer_type=AnswerType.QUESTION_SELFHANDLING)
