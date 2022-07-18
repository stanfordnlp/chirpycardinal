import random

from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponsePriority, ResponseGeneratorResult
from chirpy.response_generators.wiki2.state import ConditionalState
from chirpy.response_generators.neural_fallback.neural_helpers import get_random_fallback_neural_response
from typing import Optional
import logging
import chirpy.response_generators.wiki2.wiki_utils as wiki_utils

logger = logging.getLogger('chirpylogger')


class WikiTakeOverTreelet(Treelet):
    name = "wiki_takeover_treelet"

    def get_summary_takeover(self, related_wiki_section, sentseg_fn, max_words, max_sents):
        summary = wiki_utils.get_summary(related_wiki_section['text'], sentseg_fn, max_words, max_sents)
        logger.primary_info(f"Takeover Summary is: {summary}")
        summary = wiki_utils.clean_wiki_text(summary)
        logger.primary_info(f"Takeover Summary after clean is: {summary}")
        if wiki_utils.contains_offensive(summary):
            logger.primary_info(f"Found takeover overview to be offensive, discarding it")
            return None
        return summary

    def get_takeover_paragraph(self, cur_entity: str, takeover_entity: str) -> Optional[str]:
        related_wiki_sections_from_cur_entity_doc = wiki_utils.search_wiki_sections(cur_entity, (takeover_entity,), (takeover_entity,))
        related_wiki_sections_from_takeover_entity_doc = wiki_utils.search_wiki_sections(takeover_entity, (cur_entity,), (cur_entity,))

        logging.error(f"related_wiki_sections_from_cur_entity_doc: {related_wiki_sections_from_cur_entity_doc}")
        logging.error(f"related_wiki_sections_from_takeover_entity_doc: {related_wiki_sections_from_takeover_entity_doc}")

        if related_wiki_sections_from_cur_entity_doc:
            return self.get_summary_takeover(related_wiki_sections_from_cur_entity_doc, wiki_utils.get_sentseg_fn(self.rg), max_sents=4)

        if related_wiki_sections_from_takeover_entity_doc:
            return self.get_summary_takeover(related_wiki_sections_from_takeover_entity_doc, wiki_utils.get_sentseg_fn(self.rg), max_sents=4)

        logger.info("No overview found")
        return None

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()

        rg_that_was_taken_over = self.rg.state_manager.last_state.active_rg
        logger.error(f'RG_THAT_WAS_TAKEN_OVER: {rg_that_was_taken_over}')

        cur_entity = self.get_current_entity()
        takeover_entity = self.get_most_recent_able_to_takeover_entity()
        logger.error(f'WIKI TAKEOVER ENTITY: {takeover_entity}')

        takeover_text = "TODO:TAKEOVER_WIKI_TEXT"   # self.get_takeover_paragraph(cur_entity.name, takeover_entity.name)
        ack = random.choice([
            "Well, from what I've read,",
            "Ah, to my knowledge,"
        ])

        logger.error(f'WIKI TAKEOVER TEXT: {takeover_text}')



        if takeover_text:
            return ResponseGeneratorResult(
                text=f"{ack} {wiki_utils.clean_wiki_text(takeover_text)}",
                priority=priority,
                state=state, needs_prompt=False, cur_entity=takeover_entity,
                conditional_state=ConditionalState(prev_treelet_str=self.name,
                                                   next_treelet_str=self.rg.handback_treelet.name,
                                                   rg_that_was_taken_over=rg_that_was_taken_over),
                takeover_rg_willing_to_handback_control=True    # EDIT

            )

        else:
            return None
