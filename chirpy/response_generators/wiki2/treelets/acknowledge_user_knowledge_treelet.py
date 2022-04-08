from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponsePriority, ResponseGeneratorResult
from chirpy.response_generators.wiki2.state import ConditionalState
from chirpy.response_generators.wiki2.response_templates import AcknowledgeUserKnowledgeTemplate


class AcknowledgeUserKnowledgeTreelet(Treelet):
    name = "wiki_acknowledge_user_knowledge_treelet"

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        entity = self.rg.state.cur_entity
        return ResponseGeneratorResult(
            text=AcknowledgeUserKnowledgeTemplate().sample().format(entity.talkable_name),
            priority=ResponsePriority.STRONG_CONTINUE,
            state=self.rg.state, needs_prompt=False, cur_entity=entity,
            conditional_state=ConditionalState(prev_treelet_str=self.name,
                                               next_treelet_str=self.rg.get_opinion_treelet.name)
        )
