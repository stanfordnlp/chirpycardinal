"""
    Trenton Chang, Caleb Chiam - Nov. 2020
    possible_continue_treelet.py

    This treelet triggers when the user expresses noncommittal/disinterested feelings, and asks whether the user would
    like to continue talking to this RG.

"""
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, ResponsePriority, emptyResult
from chirpy.core.response_generator import Treelet
from chirpy.response_generators.personal_issues.state import State, ConditionalState
from chirpy.response_generators.personal_issues.personal_issues_helpers import ResponseType
from chirpy.response_generators.personal_issues.response_templates import PossibleContinueResponseTemplate, \
    ConfusedPossibleContinueResponseTemplate

import logging
logger = logging.getLogger('chirpylogger')


class PossibleContinueTreelet(Treelet):
    """
    Checks if the user wants to continue talking about his/her personal issue;
    specifically, when the user has already made some personal disclosures in previous turns,
    but is now giving noncommittal or possibly disinterested responses.

    """
    name = "personal_issues_possible_continue"

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        """Generates a ResponseGeneratorResult containing that treelet's response to the user.

        Args:
            state (State): representation of the RG's internal state; see state.py for definition.
            utterance (str): what the user just said
            response_types (Set[ResponseTypes]): type of response given by the user; see ...personal_issues/personal_issues_utils.py
                for a full definition of the ResponseTypes enum.
            priority (ResponsePriority): five-level response priority tier.

        Returns:
            ResponseGeneratorResult: an object encapsulating the textual response given by the RG, and some metadata.
        """
        state, utterance, response_types = self.get_state_utterance_response_types()
        template = PossibleContinueResponseTemplate()
        response = template.sample()
        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                             next_treelet_str='transition')
        return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=False, state=state,
                                       cur_entity=None, conditional_state=conditional_state)
