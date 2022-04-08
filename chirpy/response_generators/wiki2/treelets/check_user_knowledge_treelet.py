from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponsePriority, ResponseGeneratorResult
from chirpy.response_generators.wiki2.state import ConditionalState
from chirpy.response_generators.wiki2.response_templates import CheckUserKnowledgeTemplate

import logging
logger = logging.getLogger('chirpylogger')

class CheckUserKnowledgeTreelet(Treelet):
    name = "wiki_check_user_knowledge_treelet"

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        entity = self.rg.state.cur_entity
        ack = self.rg.get_acknowledgement(entity, allow_neural=True)

        is_person = any([cat.endswith('person') for cat in entity.wikidata_categories]) and \
                    all([not cat.endswith('company') for cat in entity.wikidata_categories])
        text = CheckUserKnowledgeTemplate().sample().format(entity.talkable_name,
                                                            is_are=['is', 'are'][int(entity.is_plural)],
                                                            some_one_thing=['something', 'someone'][int(is_person)]
                                                            )

        if ack is not None:
            text = ack + " " + text
        return ResponseGeneratorResult(
            text=text,
            priority=priority,
            state=self.rg.state, needs_prompt=False, cur_entity=entity,
            conditional_state=ConditionalState(prev_treelet_str=self.name,
                                               next_treelet_str='transition')
        )
