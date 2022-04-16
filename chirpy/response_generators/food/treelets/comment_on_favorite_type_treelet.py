import logging
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.response_generators.food.regex_templates import DoubtfulTemplate
from chirpy.core.response_generator_datatypes import PromptType, ResponseGeneratorResult, PromptResult, AnswerType
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.response_generator import Treelet
from chirpy.response_generators.food.food_helpers import *
from chirpy.core.entity_linker.entity_groups import EntityGroupsForExpectedType
from chirpy.core.util import infl
from chirpy.response_generators.food.state import State, ConditionalState

logger = logging.getLogger('chirpylogger')

class CommentOnFavoriteTypeTreelet(Treelet):
    name = "comment_on_favorite_type_treelet"

    def classify_user_response(self):
        assert False, "This should never be called."

    def get_prompt(self, conditional_state=None):
        state, utterance, response_types = self.get_state_utterance_response_types()
        logger.primary_info(f"State is {state}, conditional_state is {conditional_state}")
        entity = self.rg.get_current_entity()
        if conditional_state and conditional_state.cur_food:
            cur_food = conditional_state.cur_food
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

    def get_best_candidate_user_entity(self, utterance, cur_food):
        def condition_fn(entity_linker_result, linked_span, entity):
            return EntityGroupsForExpectedType.food_related.matches(entity) and entity.name != cur_food
        entity = self.rg.state_manager.current_state.entity_linker.top_ent(condition_fn) or self.rg.state_manager.current_state.entity_linker.top_ent()
        if entity is not None:
            user_answer = entity.talkable_name
            plural = entity.is_plural
        else:
            nouns = self.rg.state_manager.current_state.corenlp['nouns']
            if len(nouns):
                user_answer = nouns[-1]
                plural = True
            else:
                user_answer = utterance.replace('i like', '').replace('my favorite', '').replace('i love', '')
                plural = True

        return user_answer, plural

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        """ Returns the response. """
        state, utterance, response_types = self.get_state_utterance_response_types()
        entity = self.rg.get_current_entity(initiated_this_turn=False)
        cur_food_entity = state.cur_food
        cur_food = cur_food_entity.name
        cur_talkable_food = cur_food_entity.talkable_name

        user_answer, is_plural = self.get_best_candidate_user_entity(utterance, cur_food)
        copula = infl('are', is_plural)
        pronoun = infl('they', is_plural)

        if get_custom_question(cur_food) is not None:
            # try to find a food first, but if that fails, just select the top entity.
            if ResponseType.DONT_KNOW in response_types:
                response = "No worries, it can be difficult to pick just one!"
            elif ResponseType.NO in response_types:
                response = "Okay, no worries."
            else:
                response = self.rg.get_neural_response(prefix=f'{user_answer} {copula} a great choice! I especially love how {pronoun}')
                response = response.replace('!', '.').split('.')[0] + '.' # only take one sentence

            custom_question_answer = get_custom_question_answer(cur_food)
            text = f"{response} Personally, when it comes to {cur_talkable_food}, I really like {custom_question_answer}."
        else:
            # sample another of the same type
            entity = self.rg.state_manager.current_state.entity_tracker.cur_entity
            other_type = sample_from_type(cur_food)
            text = f"That totally makes sense! I also really enjoy {user_answer}. Personally, I really like {other_type}."

        return ResponseGeneratorResult(text=text, priority=priority,
                                       needs_prompt=False, state=state,
                                       cur_entity=entity,
                                       conditional_state=ConditionalState(
                                           prompt_treelet=self.rg.open_ended_user_comment_treelet.name,
                                           cur_food=cur_food_entity)
                                       )
