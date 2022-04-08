import random

from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponsePriority, ResponseGeneratorResult
from chirpy.response_generators.wiki2.state import ConditionalState
from chirpy.response_generators.neural_fallback.neural_helpers import get_random_fallback_neural_response
from typing import Optional
import logging
import chirpy.response_generators.wiki2.wiki_utils as wiki_utils

logger = logging.getLogger('chirpylogger')


class IntroEntityTreelet(Treelet):
    """
    Get an introductory paragraph for the treelet
    """
    name = "wiki_intro_entity_treelet"

    def get_intro_paragraph(self, entity: str) -> Optional[str]:
        """This method attempts to get a summary of a section. In the future this could be a real
        summarization module

        :param entity: the current resolved WIKI entity
        :type entity: str
        :return: The summary of the section. Currently LEAD-3
        :rtype: str

        >>> treelet = IntroductoryTreelet(None)
        >>> treelet.get_overview('Taylor Swift')
        'Taylor Alison Swift (born December 13, 1989) is an American singer-songwriter.
        She is known for narrative songs about her personal life, which have received widespread media coverage.'
        """
        logger.debug(f'Getting overview for: {entity}')
        overview = wiki_utils.overview_entity(entity, wiki_utils.get_sentseg_fn(self.rg), max_sents=4)
        if not overview:
            logger.info("No overview found")
            return None
        return overview

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()
        entity = state.cur_entity
        text = self.get_intro_paragraph(entity.name)
        ack = random.choice([
            "Well, from what I've read,",
            "Ah, to my knowledge,"
        ])

        if text:
            return ResponseGeneratorResult(
                text=f"{ack} {wiki_utils.clean_wiki_text(text)}",
                priority=priority,
                state=state, needs_prompt=False, cur_entity=entity,
                conditional_state=ConditionalState(prev_treelet_str=self.name,
                                                   next_treelet_str=self.rg.discuss_article_treelet.name)
            )
        else: # no intro paragraph available
            neural_response = get_random_fallback_neural_response(self.get_current_state())
            if neural_response:
                return ResponseGeneratorResult(
                    text=neural_response,
                    priority=priority,
                    state=state, needs_prompt=False, cur_entity=entity,
                    conditional_state=ConditionalState(prev_treelet_str=self.name,
                                                       next_treelet_str=self.rg.discuss_article_treelet.name)
                )

            return self.rg.discuss_article_treelet.get_response(priority=priority)
            # return ResponseGeneratorResult( # TODO or use an infilling templates?
            #     text=f"No worries, {entity.name} is pretty interesting. I could tell you about its history if you'd like.",
            #     priority=priority, # TODO pass to wiki section treelet
            #     state=state, needs_prompt=False, cur_entity=entity,
            #     conditional_state=ConditionalState(prev_treelet_str=self.name,
            #                                        next_treelet_str=None)
            # )
