import logging

from chirpy.core.response_generator import *
from chirpy.response_generators.personal_issues.state import State, ConditionalState
from chirpy.response_generators.aliens.aliens_responses import MONOLOGUES
from chirpy.response_generators.aliens.aliens_helpers import ResponseType

from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, AnswerType
logger = logging.getLogger('chirpylogger')


class SecondTurnTreelet(Treelet):
    name = "aliens_second_turn"

    def get_response(self, priority):
        state, utterance, response_types = self.get_state_utterance_response_types()
        prefix = "Exactly! " if ResponseType.YES in response_types else "Well, please let me know if this is boring to you, but "
        response = prefix + MONOLOGUES[2]
        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                             next_treelet_str=self.rg.third_turn_treelet.name)
        return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=False, state=state,
                                       cur_entity=None, conditional_state=conditional_state,
                                       answer_type=AnswerType.STATEMENT)
