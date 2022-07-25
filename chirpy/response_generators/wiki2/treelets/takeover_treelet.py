import random

from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponsePriority, ResponseGeneratorResult
from chirpy.response_generators.wiki2.state import ConditionalState
from chirpy.response_generators.neural_fallback.neural_helpers import get_random_fallback_neural_response
from typing import Optional
import logging
import chirpy.response_generators.wiki2.wiki_utils as wiki_utils


from chirpy.annotators.blenderbot import BlenderBot

logger = logging.getLogger('chirpylogger')


class WikiTakeOverTreelet(Treelet):
    name = "wiki_takeover_treelet"

    def get_response(self, priority=ResponsePriority.FORCE_START, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()

        rg_that_was_taken_over = self.rg.state_manager.last_state.active_rg
        logger.debug(f'rg that was taken over is {rg_that_was_taken_over}.')

        cur_entity = self.get_current_entity()
        takeover_entity = self.get_most_recent_able_to_takeover_entity()

        takeover_text = wiki_utils.get_takeover_text(self.rg, cur_entity, takeover_entity)

        logger.info(f"takenover_text is {takeover_text}")

        if takeover_text:
            intro_intersect_text = wiki_utils.get_random_intro_intersect_text(cur_entity.talkable_name, takeover_entity.talkable_name)
            starter_text = wiki_utils.get_random_starter_text()
            return ResponseGeneratorResult(
                text=intro_intersect_text + starter_text + takeover_text,
                priority=priority,
                state=state, needs_prompt=False, cur_entity=takeover_entity,
                conditional_state=ConditionalState(prev_treelet_str=self.name,
                                                   next_treelet_str=self.rg.handback_treelet.name,
                                                   rg_that_was_taken_over=rg_that_was_taken_over,
                                                   takeover_entity=takeover_entity),
                takeover_rg_willing_to_handback_control=True
            )

        else:
            neural_prefix = f'Speaking of {takeover_entity.talkable_name} and {cur_entity.talkable_name},'
            takeover_neural_response = self.rg.get_neural_response(prefix=neural_prefix)
            takeover_neural_response = takeover_neural_response.split('.')[0]
            generated_response = takeover_neural_response[len(neural_prefix):]
            logger.info(f"takenover_neural_response is {takeover_neural_response}")
            if takeover_entity.talkable_name in generated_response  and cur_entity.talkable_name in generated_response:
                intro_intersect_text = wiki_utils.get_random_intro_intersect_text(cur_entity.talkable_name,
                                                                                  takeover_entity.talkable_name)
                logger.info("takenover_neural_response is used.")
                starter_text = wiki_utils.get_random_starter_text()
                return ResponseGeneratorResult(
                    text=intro_intersect_text + starter_text + generated_response,
                    priority=priority,
                    state=state, needs_prompt=False, cur_entity=takeover_entity,
                    conditional_state=ConditionalState(prev_treelet_str=self.name,
                                                   next_treelet_str=self.rg.handback_treelet.name,
                                                   rg_that_was_taken_over=rg_that_was_taken_over,
                                                   takeover_entity=takeover_entity),
                    takeover_rg_willing_to_handback_control=True
                )
            else:
                logger.info("takenover_neural_response is not used because it does not contain takeover_entity and cur_entity in it.")
                logger.info(
                    "WIKI fails to takeover.")
                return None