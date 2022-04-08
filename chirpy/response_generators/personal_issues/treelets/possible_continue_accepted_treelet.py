"""
    Trenton Chang, Caleb Chiam - Nov. 2020
    possible_continue_accepted_treelet.py

    This treelet redirects the conversation back to the user's personal issues, and is used to smoothly transition
    back into the conversation after the user expresses noncommittal/disinterested feelings but confirms a desire
    to continue talking to this RG.

"""
from chirpy.core.response_generator import Treelet
from chirpy.response_generators.personal_issues.state import State, ConditionalState
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, ResponsePriority, emptyResult
from chirpy.response_generators.personal_issues.response_templates import PossibleContinueAcceptedResponseTemplate

import logging
logger = logging.getLogger('chirpylogger')

"""POSSIBLE_CONTINUE_ACCEPTED_RESPONSES = [
    "Okay. I'm happy to keep talking.",
    "Okay. Feel free to keep telling me more.",
    "Sounds good. Feel free to tell me more.",
    "All right. What else did you want to bring up?"
]"""

class PossibleContinueAcceptedTreelet(Treelet):
    """
    Prompts user to keep talking if they previously indicated they would like to continue the conversation
    """
    name = "personal_issues_possible_continue_accepted"


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
        template = PossibleContinueAcceptedResponseTemplate()
        response = template.sample()
        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                             next_treelet_str='transition')
        return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=False, state=state,
                                       cur_entity=None, conditional_state=conditional_state)
