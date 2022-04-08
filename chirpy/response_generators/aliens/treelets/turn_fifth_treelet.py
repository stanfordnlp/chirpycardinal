import logging

from chirpy.core.response_generator import *
from chirpy.response_generators.aliens.state import State, ConditionalState
from chirpy.response_generators.aliens.aliens_responses import MONOLOGUES, ACKNOWLEDGMENTS
from chirpy.response_generators.aliens.aliens_helpers import ResponseType

from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, AnswerType

from random import choice
logger = logging.getLogger('chirpylogger')


class FifthTurnTreelet(Treelet):
    name = "aliens_fifth_turn"

    def get_response(self, priority):
        state, utterance, response_types = self.get_state_utterance_response_types()
        response = MONOLOGUES[5]
        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                             next_treelet_str=None)
        prefix = choice(ACKNOWLEDGMENTS) + ' ' if ResponseType.OPINION in response_types else 'Yeah, '
        return ResponseGeneratorResult(text=prefix+response, priority=priority, needs_prompt=False, state=state,
                                       cur_entity=None, conditional_state=conditional_state,
                                       answer_type=AnswerType.STATEMENT)
