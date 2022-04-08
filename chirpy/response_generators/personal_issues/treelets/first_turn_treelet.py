"""
    Trenton Chang, Caleb Chiam - Nov. 2020
    first_turn_treelet.py

    The following treelet initiates the conversation about personal issues when prompted by the user (i.e. a negative
    personal disclosure was detected).
"""
import logging

# RG IMPORTS
from chirpy.response_generators.personal_issues.response_templates.first_turn_response_template import FirstTurnResponseTemplate
from chirpy.core.response_generator import *
from chirpy.response_generators.personal_issues.state import State, ConditionalState

# CORE MODULE IMPORTS
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult
logger = logging.getLogger('chirpylogger')


class FirstTurnTreelet(Treelet):
    name = "personal_issues_first_turn"

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        """Generates a ResponseGeneratorResult containing that treelet's response to the user.

        Args:
            state (State): representation of the RG's internal state; see state.py for definition.
            utterance (str): what the user just said
            response_types (ResponseTypes): type of response given by the user; see ...personal_issues/personal_issues_utils.py
                for a full definition of the ResponseTypes enum.
            priority (ResponsePriority): five-level response priority tier.

        Returns:
            ResponseGeneratorResult: an object encapsulating the textual response given by the RG, and some metadata.
        """
        state, utterance, response_types = self.get_state_utterance_response_types()
        template = FirstTurnResponseTemplate()
        response = template.sample()
        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                             next_treelet_str='transition')
        return ResponseGeneratorResult(text=response, priority=priority,
                                       needs_prompt=False, state=state,
                                       cur_entity=None, conditional_state=conditional_state)



