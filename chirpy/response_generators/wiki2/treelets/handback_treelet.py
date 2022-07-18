import random

from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponsePriority, ResponseGeneratorResult
from chirpy.response_generators.wiki2.state import ConditionalState
from chirpy.response_generators.neural_fallback.neural_helpers import get_random_fallback_neural_response
from typing import Optional
import logging
import chirpy.response_generators.wiki2.wiki_utils as wiki_utils

logger = logging.getLogger('chirpylogger')


class WikiHandBackTreelet(Treelet):
    name = "wiki_handback_treelet"

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()


        logger.error(f'WIKI HANDBACK')


        return ResponseGeneratorResult(
            text="TODO:HANDBACK_WIKI_TEXT (WRAP UP)",
            priority=priority,
            state=state, needs_prompt=True, cur_entity=self.get_current_entity(),
            conditional_state=ConditionalState(prev_treelet_str=self.name,
                                                next_treelet_str=None,
                                                rg_that_was_taken_over=self.rg.state.rg_that_was_taken_over),
            )

