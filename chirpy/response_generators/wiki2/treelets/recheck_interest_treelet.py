from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponsePriority, ResponseGeneratorResult
from chirpy.response_generators.wiki2.state import ConditionalState
from chirpy.response_generators.wiki2.response_templates.response_components import DISCUSS_FURTHER_QUESTION
import logging
import random

logger = logging.getLogger('chirpylogger')


class RecheckInterestTreelet(Treelet):
    """
    Activates after user says "No" to Factoid / Infiller / AcknowledgeUserKnowledge
    """
    name = "recheck_interest_treelet"

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        entity = self.rg.state.cur_entity
        text = random.choice([
            "Oh, I hope I didn't make a mistake in explaining that.",
            "Hmm, sometimes I get things wrong so I might have made a mistake!"
        ])
        qn = random.choice(DISCUSS_FURTHER_QUESTION)
        return ResponseGeneratorResult(
            text=f"{text} {qn.format(entity.name)}",
            priority=priority,
            state=self.rg.state, needs_prompt=False, cur_entity=entity,
            conditional_state=ConditionalState(prev_treelet_str=self.name,
                                               next_treelet_str='transition')
        )
