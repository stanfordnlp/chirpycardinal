import logging
from random import choice

from chirpy.core.entity_linker.entity_linker_simple import get_entity_by_wiki_name
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, ResponsePriority, emptyResult, PromptResult, PromptType, emptyPrompt
from chirpy.response_generators.categories.classes import Treelet, ConditionalState, State
from chirpy.response_generators.categories.categories import HistoryCategory
from chirpy.response_generators.categories.treelets.handle_answer_treelet import HandleAnswerTreelet


logger = logging.getLogger('chirpylogger')

ACKNOWLEDGEMENTS = [
    "Ok. Can do!",
    "Cool!",
    "Awesome!",
    "Great!",
    "Works for me!",
]

BRIDGES = [
    "So,",
    "I'd love to hear,",
    "Anyway,",
]


class IntroductoryTreelet(Treelet):

    def get_response(self, state: State, state_manager) -> ResponseGeneratorResult:
        """Ask the first unasked question for state.cur_category_name"""

        category_name = state.cur_category_name
        question = state.get_first_category_response(category_name, state_manager)  # CategoryQuestion or None
        if question:
            question_str = None
            if question.statement is None:
                question_str = question.question
            elif question.question is None:
                question_str = question.statement
            else:
                question_str = ' '.join((question.statement, question.question))
            response = "{} {}".format(choice(ACKNOWLEDGEMENTS), question_str)
            priority = ResponsePriority.CAN_START if category_name == HistoryCategory.__name__ else ResponsePriority.FORCE_START
            cur_entity = get_entity_by_wiki_name(question.cur_entity_wiki_name, state_manager.current_state)
            conditional_state = ConditionalState(HandleAnswerTreelet.__name__, category_name, question.statement, question.question, False)
            return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=False, state=state,
                                           cur_entity=cur_entity, expected_type=question.expected_type,
                                           conditional_state=conditional_state)
        else:
            return emptyResult(state)


    def get_prompt(self, state: State, state_manager) -> PromptResult:
        """Ask the first unasked question for state.cur_category_name"""

        category_name = state.cur_category_name
        question = state.get_first_unasked_question(category_name)  # CategoryQuestion or None
        if question:
            question_str = question.question
            response = "{} {}".format(choice(BRIDGES), question_str)
            cur_entity = get_entity_by_wiki_name(question.cur_entity_wiki_name, state_manager.current_state)
            conditional_state = ConditionalState(HandleAnswerTreelet.__name__, category_name, None, question_str, False)
            return PromptResult(text=response, prompt_type=PromptType.CURRENT_TOPIC, state=state, cur_entity=cur_entity,
                         expected_type=question.expected_type, conditional_state=conditional_state)
        else:
            return emptyPrompt(state)