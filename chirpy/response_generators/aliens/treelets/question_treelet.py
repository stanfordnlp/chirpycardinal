import logging

from chirpy.core.response_generator import *
from chirpy.response_generators.aliens.aliens_responses import QUESTION_RESPONSE
from chirpy.core.response_priority import ResponsePriority, PromptType

from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, AnswerType
logger = logging.getLogger('chirpylogger')


class QuestionTreelet(Treelet):
    name = "aliens_question"

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        response = QUESTION_RESPONSE
        state, utterance, response_types = self.get_state_utterance_response_types()
        conditional_state = self.rg.ConditionalState(prev_treelet_str=self.name,
                                                     next_treelet_str='transition')
        return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=False, state=state,
                                       cur_entity=None, conditional_state=conditional_state,
                                       answer_type=AnswerType.STATEMENT)

    def get_question_response(self):
        return self.get_response(ResponsePriority.STRONG_CONTINUE, )
