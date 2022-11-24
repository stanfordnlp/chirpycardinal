import logging
from typing import Optional
import copy

from chirpy.core.response_generator import ResponseGenerator, SymbolicTreelet
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.response_generator_datatypes import emptyResult, ResponseGeneratorResult, PromptResult, emptyPrompt, \
    UpdateEntity, AnswerType
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
from chirpy.response_generators.food.regex_templates import *
from chirpy.core.regex.util import OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST

from chirpy.response_generators.food.treelets.introductory_treelet import IntroductoryTreelet
# from chirpy.response_generators.food.treelets.get_other_type_treelet import GetOtherTypeTreelet
from chirpy.response_generators.food.treelets.open_ended_user_comment_treelet import OpenEndedUserCommentTreelet
from chirpy.response_generators.food.treelets.comment_on_favorite_type_treelet import CommentOnFavoriteTypeTreelet
from chirpy.response_generators.food.treelets.factoid_treelet import FactoidTreelet
from chirpy.response_generators.food.treelets.ask_favorite_food_treelet import AskFavoriteFoodTreelet
from chirpy.response_generators.food.state import State, ConditionalState
from chirpy.core.offensive_classifier.offensive_classifier import OffensiveClassifier
from chirpy.response_generators.food.food_helpers import *

logger = logging.getLogger('chirpylogger')

class FoodResponseGenerator(ResponseGenerator):
    name='FOOD'

    def __init__(self, state_manager) -> None:
        self.god_treelet = SymbolicTreelet(self, 'food')
        treelets = {treelet.name: treelet for treelet in [self.god_treelet]}
        super().__init__(state_manager, treelets=treelets, intent_templates=[], can_give_prompts=True,
                         state_constructor=State,
                         conditional_state_constructor=ConditionalState,
                         trigger_words=["food"])

    def identify_response_types(self, utterance):
        response_types = super().identify_response_types(utterance)

        if is_recognized_food(self, utterance):
            response_types.add(ResponseType.RECOGNIZED_FOOD)

        if is_unknown_food(self, utterance):
            response_types.add(ResponseType.UNKNOWN_FOOD)

        return response_types

    def get_treelet_for_entity(self, entity):
        # logger.primary_info("Get_treelet_for_entity was called")
        # if entity.name == 'Food':
        #     return AskFavoriteFoodTreelet(self).name
        # logger.primary_info(f"Food had its get_treelet_for_entity called: {is_known_food(entity.name.lower())}")
        # if is_known_food(entity.name.lower()):
        #     return IntroductoryTreelet(self).name
        # else:
        #     return None # can't handle this food entity
        if entity.name == 'Food' or is_known_food(entity.name.lower()):
            return self.god_treelet.name
        return None


    def handle_rejection_response(self, prefix='', main_text=None, suffix='',
                                  priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                  conditional_state=None, answer_type=AnswerType.ENDING):
        return super().handle_rejection_response(
            prefix="I'm sorry, food is a little different here in the cloud, so I might've said something weird.",
            main_text=main_text,
            suffix=suffix,
            priority=priority,
            needs_prompt=needs_prompt,
            conditional_state=conditional_state,
            answer_type=answer_type
        )

    def get_neural_response(self, prefix=None, allow_questions=False, conditions=None) -> Optional[str]:
        if conditions is None: conditions = []
        offensive_classifier = OffensiveClassifier()
        conditions = [lambda response: not offensive_classifier.contains_offensive(response),
                      lambda response: not any(bad in response for bad in BAD_WORDS)] + conditions
        response = super().get_neural_response(prefix, allow_questions, conditions)
        if response is None: return "That's great to hear."
        return response

    def get_prompt(self, state):
        self.state = state
        self.response_types = self.get_cache(f'{self.name}_response_types')
        return self.emptyPrompt()

    def check_and_set_entry_conditions(self, state):
        cur_state = copy.copy(state)
        entity = self.get_current_entity(initiated_this_turn=True)
        if entity.name == 'Food':
            cur_state.entry_entity_is_food = True
        elif is_known_food(entity.name.lower()):
            cur_state.cur_entity_known_food = True
        return cur_state
