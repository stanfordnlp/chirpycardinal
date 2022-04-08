"""
    Trenton Chang, Caleb Chiam - Nov. 2020
    subsequent_turn_treelet.py

    This treelet is where the bulk of the conversation with this RG will be. At a high-level, it responds empathetically
    to the user and indicates that it is listening to the user's disclosures. It is intended to be an ELIZA++ simulation
    of active listening techniques.

"""

from chirpy.core.response_generator import *
from chirpy.response_generators.personal_issues.state import State, ConditionalState
from chirpy.response_generators.personal_issues.response_templates import *
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, ResponsePriority
from chirpy.response_generators.personal_issues.personal_issues_helpers import *
from chirpy.response_generators.personal_issues.response_templates.response_components import *

import logging
import random
logger = logging.getLogger('chirpylogger')

USE_NEURAL_CHAT = True

class SubsequentTurnTreelet(Treelet):
    name = "personal_issues_subsequent_turn"

    def __init__(self, *args):
        super(SubsequentTurnTreelet, self).__init__(*args)
        # self.pp = TemplateBasedParaphraser()

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        """Generates a ResponseGeneratorResult containing that treelet's response to the user.

        Args:
            state (State): representation of the RG's internal state; see state.py for definition.
            utterance (str): what the user just said
            response_types (Set[ResponseTypes]): set of response types given by the user; see ...personal_issues/personal_issues_utils.py
                for a full definition of the ResponseTypes enum.
            priority (ResponsePriority): five-level response priority tier.

        Returns:
            ResponseGeneratorResult: an object encapsulating the textual response given by the RG, and some metadata.
        """
        state, utterance, response_types = self.get_state_utterance_response_types()
        if ResponseType.SHORT_RESPONSE in response_types: # handle super-short responses like 'okay', 'yep'
            response = random.choice(STATEMENTS_LISTEN_SHORT)
            conditional_state = ConditionalState(prev_treelet_str=self.name,
                                                 next_treelet_str='transition',
                                                 question_last_turn='?' in response)

            return ResponseGeneratorResult(text=random.choice(STATEMENTS_LISTEN_SHORT),
                                           priority=priority,
                                           needs_prompt=False, state=state, cur_entity=None,
                                           conditional_state=conditional_state)

        response = ""
        neural_chat_used = False
        if state.question_last_turn:
            response = ValidationResponseTemplate().sample()
        else:
            if not state.neural_last_turn:
                gpt_response = self.rg.get_neural_response(prefix=GPTPrefixResponseTemplate().sample())
                if gpt_response is None:
                    template = SubsequentTurnResponseTemplate()
                    response = template.sample()
                else:
                    response += gpt_response
                    neural_chat_used = True
                    response += " " + PartialSubsequentTurnResponseTemplate().sample()
            else:
                response = SubsequentTurnResponseTemplate().sample()

        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                             next_treelet_str='transition',
                                             neural_last_turn=neural_chat_used,
                                             question_last_turn='?' in response)

        return ResponseGeneratorResult(text=response, priority=priority,
                                       needs_prompt=False, state=state, cur_entity=None,
                                       conditional_state=conditional_state)
