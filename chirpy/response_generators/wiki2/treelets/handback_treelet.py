import random

from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponsePriority, ResponseGeneratorResult
from chirpy.response_generators.wiki2.state import ConditionalState
from chirpy.response_generators.neural_fallback.neural_helpers import get_random_fallback_neural_response
from typing import Optional
import logging

import chirpy.response_generators.wiki2.wiki_utils as wiki_utils
from chirpy.response_generators.wiki2.wiki_helpers import ResponseType
from chirpy.core.regex.response_lists import *
from chirpy.response_generators.wiki2.response_templates.response_components import *

logger = logging.getLogger('chirpylogger')


class WikiHandBackTreelet(Treelet):
    name = "wiki_handback_treelet"

    def get_acknowledgement(self):
        state, utterance, response_types = self.get_state_utterance_response_types()
        if ResponseType.CONFUSED in response_types: return random.choice(ERROR_ADMISSION)

        prefix = ''
        if ResponseType.AGREEMENT in response_types:
            return random.choice(RESPONSES_TO_USER_AGREEMENT)
        if ResponseType.POS_SENTIMENT in response_types:
            if ResponseType.OPINION in response_types:
                prefix = random.choice(POS_OPINION_RESPONSES)
            elif ResponseType.APPRECIATIVE in response_types:
                return random.choice(APPRECIATION_DEFAULT_ACKNOWLEDGEMENTS)
        elif ResponseType.NEG_SENTIMENT in response_types:
            if ResponseType.OPINION in response_types: # negative opinion
                prefix = "That's an interesting take,"
            else: # expression of sadness
                return random.choice(COMMISERATION_ACKNOWLEDGEMENTS)
        elif ResponseType.NEUTRAL_SENTIMENT in response_types:
            if ResponseType.OPINION in response_types or ResponseType.PERSONAL_DISCLOSURE in response_types:
                return random.choice(NEUTRAL_OPINION_SHARING_RESPONSES)
        elif ResponseType.KNOW_MORE:
            return "Yeah,"
        if prefix is not None:
            return prefix
        return random.choice(POST_SHARING_ACK)

    def get_response(self, priority=ResponsePriority.FORCE_START, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()
        takeover_entity = state.takeover_entity

        logger.debug(f'WIKI handback_treelet is triggered.')

        wrap_up_text = self.get_acknowledgement()

        return ResponseGeneratorResult(
                text=wrap_up_text,
                priority=priority,
                state=state, needs_prompt=True, cur_entity=self.get_current_entity(),
                conditional_state=ConditionalState(prev_treelet_str=self.name,
                                                   next_treelet_str=None,
                                                   rg_that_was_taken_over=self.rg.state.rg_that_was_taken_over,
                                                   takeover_entity=takeover_entity),
            )

