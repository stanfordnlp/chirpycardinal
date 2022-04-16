from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponsePriority, ResponseGeneratorResult
from chirpy.response_generators.wiki2.state import ConditionalState
import logging

logger = logging.getLogger('chirpylogger')


class FactoidTreelet(Treelet):
    """
    Get a factoid about the entity
    """
    name = "wiki_factoid_treelet"

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        entity = self.rg.state.cur_entity
        state, utterance, response_types = self.get_state_utterance_response_types()
        top_res, top_ack = self.rg.get_infilling_statement(entity)
        logger.info(f"Top res is: {top_res}")
        logger.info(f"Top ack is: {top_ack}")
        if top_res is not None:
            return ResponseGeneratorResult(
                text=f"Cool, {top_res}. What are your thoughts on {entity.talkable_name}?",
                priority=priority,
                state=self.rg.state, needs_prompt=False, cur_entity=entity,
                conditional_state=ConditionalState(prev_treelet_str=self.name,
                                                   next_treelet_str='transition')
            )
        else:
            if kwargs.get('redirect', False):
                return self.rg.check_user_knowledge_treelet.get_response(priority=priority)
            else:
                return self.rg.combined_til_treelet.get_response(priority=priority, redirect=True)
