import logging
from random import choice

from chirpy.core.entity_linker.entity_linker_simple import get_entity_by_wiki_name
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, ResponsePriority, PromptResult, PromptType, AnswerType
from chirpy.response_generators.categories.categories import HistoryCategory
from chirpy.core.response_generator import *
from chirpy.response_generators.categories.state import ConditionalState

logger = logging.getLogger('chirpylogger')

ACKNOWLEDGEMENTS = ["Ok. Can do!", "Cool!", "Awesome!", "Great!", "Works for me!"]

BRIDGES = ["So, I was just thinking,", "I'd love to hear,", "Anyway, I was wondering,"]


class IntroductoryTreelet(Treelet):
    name = 'categories_introductory_treelet'

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        """Ask the first unasked question for state.cur_category_name"""
        logger.primary_info(f"Entered {self.name} for response generation")
        state, utterance, response_types = self.get_state_utterance_response_types()
        state_manager = self.rg.state_manager
        category_name = state.cur_category_name
        question = state.get_first_category_response(category_name, state_manager)  # CategoryQuestion or None
        if question:
            if question.statement is None:
                question_str = question.question
            elif question.question is None:
                question_str = question.statement
            else:
                question_str = ' '.join((question.statement, question.question))
            response = f"{self.choose(ACKNOWLEDGEMENTS)} {question_str}"
            priority = ResponsePriority.CAN_START if category_name == HistoryCategory.__name__ else ResponsePriority.FORCE_START
            # cur_entity = get_entity_by_wiki_name(question.cur_entity_wiki_name, state_manager.current_state)
            conditional_state = ConditionalState(
                prev_treelet_str=self.name,
                next_treelet_str=self.rg.handle_answer_treelet.name,
                cur_category_name=category_name,
                statement=question.statement,
                question=question.question,
                just_asked=False)
            return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=False, state=state,
                                           cur_entity=None, expected_type=question.expected_type,
                                           conditional_state=conditional_state, answer_type=AnswerType.QUESTION_HANDOFF)


    def get_prompt(self, **kwargs):
        """Ask the first unasked question for state.cur_category_name
        :param **kwargs:
        """
        state, utterance, response_types = self.get_state_utterance_response_types()
        state_manager = self.rg.state_manager
        category_name = state.cur_category_name
        question = state.get_first_unasked_question(category_name)  # CategoryQuestion or None
        if question:
            question_str = question.question
            response = f"{choice(BRIDGES)} {question_str}"
            # cur_entity = get_entity_by_wiki_name(question.cur_entity_wiki_name, state_manager.current_state)
            conditional_state = ConditionalState(
                prev_treelet_str=self.name,
                next_treelet_str=self.rg.handle_answer_treelet.name,
                cur_category_name=category_name,
                statement=None,
                question=question_str,
                just_asked=False)
            return PromptResult(text=response, prompt_type=PromptType.CURRENT_TOPIC, state=state, cur_entity=None,
                                expected_type=question.expected_type, conditional_state=conditional_state, answer_type=AnswerType.QUESTION_HANDOFF)
        else:
            return self.emptyPrompt()
