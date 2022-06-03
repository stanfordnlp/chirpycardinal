import logging
from typing import Optional

from chirpy.core.response_generator import ResponseGenerator

from chirpy.core.response_priority import PromptType
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyPrompt, emptyResult, \
    UpdateEntity, ResponsePriority, AnswerType
from chirpy.response_generators.categories.state import State, ConditionalState
from chirpy.response_generators.categories.treelets.introductory_treelet import IntroductoryTreelet
from chirpy.response_generators.categories.treelets.handle_answer_treelet import HandleAnswerTreelet
from chirpy.core.entity_linker.entity_linker_simple import get_entity_by_wiki_name
from chirpy.core.smooth_handoffs import SmoothHandoff
from chirpy.response_generators.categories.categories import HistoryCategory
from chirpy.response_generators.categories.categories_helpers import *

logger = logging.getLogger('chirpylogger')


class CategoriesResponseGenerator(ResponseGenerator):
    name='CATEGORIES'

    def __init__(self, state_manager) -> None:
        self.introductory_treelet = IntroductoryTreelet(self)
        self.handle_answer_treelet = HandleAnswerTreelet(self)
        treelets = {treelet.name: treelet for treelet in [self.introductory_treelet, self.handle_answer_treelet]}

        super().__init__(state_manager, treelets=treelets, state_constructor=State,
                         conditional_state_constructor=ConditionalState)

    def handle_direct_navigational_intent(self):
        # If the user is requesting a category, use introductory to generate a response
        user_initiated_category, user_has_posnav = get_user_initiated_category(self.utterance, self.state_manager.current_state)
        response = None
        if user_initiated_category is not None:
            self.state.cur_category_name = user_initiated_category
            logger.primary_info(f'Getting response from {self.introductory_treelet.name}')
            response = self.introductory_treelet.get_response()
            if response:
                if response.priority == ResponsePriority.FORCE_START and not user_has_posnav:
                    logger.primary_info("Setting response priority to CAN_START as the user does not have posnav")
                    response.priority = ResponsePriority.CAN_START
        return response


    def get_prompt(self, state: State) -> PromptResult:
        """
        Randomly choose an undiscussed generic category and ask its first question.
        """
        self.state = state
        self.response_types = self.get_cache(f'{self.name}_response_types')

        # If this is a smooth transition from movies, get a prompt for tv category from the Introductory treelet
        if self.state_manager.current_state.smooth_handoff == SmoothHandoff.MOVIES_TO_CATEGORIES:
            logger.primary_info('Getting prompt from tv IntroductoryTreelet.')
            state.cur_category_name = 'TVCategory'
            question = state.get_first_unasked_question(state.cur_category_name)
            if question is None:
                logger.warning('Unable to complete smooth handoff from movies to categories because we have no unasked tv questions left')
            else:
                # new_entity = get_entity_by_wiki_name(question.cur_entity_wiki_name, self.state_manager.current_state)
                conditional_state = ConditionalState(
                    next_treelet_str=self.handle_answer_treelet.name,
                    cur_category_name=state.cur_category_name, statement=None,
                    question=question.question, just_asked=False
                )
                result = PromptResult(text=question.question, prompt_type=PromptType.FORCE_START, state=state,
                                      cur_entity=None, # new_entity
                                      expected_type=question.expected_type, conditional_state=conditional_state)
                return result

        # If the user is requesting a category, get a prompt for that category from the Introductory treelet
        utterance = self.utterance
        user_initiated_category, user_has_posnav = get_user_initiated_category(utterance, self.get_current_state())
        if user_initiated_category is not None:
            state.cur_category_name = user_initiated_category
            logger.primary_info(f'Getting prompt from {self.introductory_treelet.name}')
            prompt_result = self.introductory_treelet.get_prompt()
            if prompt_result.text is not None and not user_has_posnav:
                logger.primary_info("Setting prompt type to CONTEXTUAL as the user does not have posnav")
                prompt_result.type = PromptType.CONTEXTUAL
            if prompt_result:
                return prompt_result

        # Ask any remaining unasked generic category questions
        category_name, question = state.get_random_generic_undiscussed_category_question()
        if category_name and question:
            logger.primary_info(f"Randomly chose an undiscussed generic category {category_name}. Asking its first question as a generic prompt.")
            # new_entity = get_entity_by_wiki_name(question.cur_entity_wiki_name, self.state_manager.current_state)
            conditional_state = ConditionalState(next_treelet_str=self.handle_answer_treelet.name,
                                                 cur_category_name=category_name,
                                                 statement=None, question=question.question, just_asked=False)
            transition = self.choose(QUESTION_CONNECTORS)
            result = PromptResult(text=transition + question.question, prompt_type=PromptType.GENERIC, state=state,
                                  cur_entity=None, expected_type=question.expected_type,
                                  conditional_state=conditional_state, answer_type=AnswerType.QUESTION_HANDOFF)

            # logger.primary_info(f"CATEGORIES prompt result is {result}")
            # print(f"Categories prompt result is {result}")
            return result

        # Otherwise return nothing
        return self.emptyPrompt()

    def update_state_if_chosen(self, state: State, conditional_state: Optional[ConditionalState]):
        state = super().update_state_if_chosen(state, conditional_state)
        statement = conditional_state.statement
        if statement:
            statement_counter = state.statements_used[conditional_state.cur_category_name]
            statement_counter[statement] += 1
            if statement_counter[statement] > 1:
                logger.warning(f'Used the same statement {statement_counter[statement]} times: {statement}')
        question = conditional_state.question
        if question:
            question_counter = state.questions_used[conditional_state.cur_category_name]
            question_counter[question] += 1
            if question_counter[question] > 1:
                logger.warning(f'Asked same question {question_counter[question]} times: {question}')
        return state
