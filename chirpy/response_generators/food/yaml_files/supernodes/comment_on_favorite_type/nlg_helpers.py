from chirpy.response_generators.food.state import State, ConditionalState
from chirpy.response_generators.food.food_helpers import *
from chirpy.core.response_generator_datatypes import AnswerType, PromptResult
from chirpy.core.response_generator import nlg_helper
from chirpy.core.response_priority import PromptType
from chirpy.core.entity_linker.entity_groups import EntityGroupsForExpectedType
from chirpy.core.util import infl

@nlg_helper
def get_prompt_for_fav_food_type(rg, conditional_state=None):
    state, utterance, response_types = rg.get_state_utterance_response_types()
    entity = rg.get_current_entity()
    if conditional_state and conditional_state.cur_food:
        cur_food = conditional_state.cur_food
    else:
        if conditional_state:
            conditional_state = ConditionalState(cur_supernode=conditional_state.cur_supernode)
        else:
            conditional_state = ConditionalState()
        cur_food = state.cur_food
    custom_question = get_custom_question(cur_food.name.lower())

    if custom_question is not None:
        text = custom_question
    # things that are subclassable, e.g. cheese.
    elif is_subclassable(cur_food.name.lower()):
        text = f"What type of {cur_food.talkable_name} do you like the most?"
    else:
        return None

    return PromptResult(text, PromptType.CONTEXTUAL, state, conditional_state=conditional_state,
                            cur_entity=entity, answer_type=AnswerType.QUESTION_SELFHANDLING)

def get_best_candidate_user_entity(rg, utterance, cur_food):
    def condition_fn(entity_linker_result, linked_span, entity):
        return EntityGroupsForExpectedType.food_related.matches(entity) and entity.name != cur_food
    entity = rg.state_manager.current_state.entity_linker.top_ent(condition_fn) or rg.state_manager.current_state.entity_linker.top_ent()
    if entity is not None:
        user_answer = entity.talkable_name
        plural = entity.is_plural
    else:
        nouns = rg.state_manager.current_state.corenlp['nouns']
        if len(nouns):
            user_answer = nouns[-1]
            plural = True
        else:
            user_answer = utterance.replace('i like', '').replace('my favorite', '').replace('i love', '')
            plural = True

    return user_answer, plural

@nlg_helper
def get_neural_response_food_type(rg):
    state, utterance, response_types = rg.get_state_utterance_response_types()
    user_answer, is_plural = get_best_candidate_user_entity(rg, utterance, state.cur_food.name)
    copula = infl('are', is_plural)
    pronoun = infl('they', is_plural)
    prefix = f'{user_answer} {copula} a great choice! I especially love how {pronoun}'
    resp = rg.get_neural_response(prefix=prefix)
    resp = resp.replace('!', '.').split('.')[0] + '.' # only take one sentence
    return resp

@nlg_helper
def get_custom_q_answer(rg):
    state, utterance, response_types = rg.get_state_utterance_response_types()
    custom_question_answer = get_custom_question_answer(state.cur_food.name)
    return custom_question_answer

@nlg_helper
def get_cur_talkable_food(rg):
    state, utterance, response_types = rg.get_state_utterance_response_types()
    return state.cur_food.talkable_name

@nlg_helper
def get_user_answer(rg):
    state, utterance, response_types = rg.get_state_utterance_response_types()
    user_answer, is_plural = get_best_candidate_user_entity(rg, utterance, state.cur_food.name)
    return user_answer

@nlg_helper
def comment_on_other_food_type(rg):
    state, utterance, response_types = rg.get_state_utterance_response_types()
    other_type = sample_from_type(state.cur_food.name)
    return other_type
