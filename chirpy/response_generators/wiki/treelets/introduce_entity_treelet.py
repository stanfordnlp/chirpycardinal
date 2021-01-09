import random
import logging
from typing import Optional

from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.latency import measure
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import NONEMPTY_TEXT, OPTIONAL_TEXT_PRE
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult
from chirpy.response_generators.wiki.treelets.abstract_treelet import Treelet, HANDOVER_TEXTS
import chirpy.response_generators.wiki.wiki_utils as wiki_utils
from chirpy.response_generators.wiki.dtypes import State, CantContinueResponseError, CantRespondError, ConditionalState, \
    CantPromptError
from chirpy.core.entity_linker.entity_linker_simple import get_entity_by_wiki_name

logger = logging.getLogger('chirpylogger')

ENTITY_INTRODUCTION_TEMPLATES = [
"So, backing up a bit, I remember you mentioned {entity_name}. Would you like to talk more about it?",
"Hmm, so, a while ago, you seemed interested in talking about {entity_name}. Would you like to talk about it?",
"Oh hey, going back! Do you remember, we started talking about {entity_name}? Want to continue chatting about it?",
]

AGREED = ['Great!', "Awesome!", "Cool!", "Sounds good!"]
ABMIGUOUS = ["I didn't exactly understand what you said, but let's just move on.",
             "Sorry, I didn't quite get it. I guess we could just talk about something else."]


class IntroduceEntityTreelet(Treelet):
    """The only job of this treelet is to introduce new entities into the discussion.
    It can be based on
    1) Existing entities that the user mentioned but haven't been talked about
    2) If we know some good wiki entities to start talking about (this hasn't yet been implemented)"""

    def __repr__(self):
        return "Introduce Entity Treelet (WIKI)"

    def __name__(self):
        return "introduce entity"

    def introduce_entity(self, state: State, is_blm=False):
        latest_untalked_entity = None
        text = None
        if is_blm:
            latest_untalked_entity = get_entity_by_wiki_name("Black Lives Matter")
            text = "I am proud to support the Black Lives Matter movement. Would you like to learn more about Black Lives Matter?"
        else:
            latest_untalked_entity = self.rg.get_untalked_entity(state)
            text = self.rg.state_manager.current_state.choose_least_repetitive(ENTITY_INTRODUCTION_TEMPLATES).format(entity_name=latest_untalked_entity.common_name)
        conditional_state = ConditionalState(
                    cur_doc_title=latest_untalked_entity.name,
                    responding_treelet=self.__repr__(),
                    prompt_handler=self.__repr__())
        return latest_untalked_entity, text, conditional_state

    def continue_response(self, base_response_result: ResponseGeneratorResult,
                          new_entity=None) -> ResponseGeneratorResult:
        #Instead can always come back later to talk about untalked entities
        raise CantContinueResponseError("WIKI has already been talking. So do not continue response with another entity.")

    @measure
    def handle_prompt(self, state: State) -> ResponseGeneratorResult:
        utterance = self.rg.state_manager.current_state.text.lower()
        last_entity = self.rg.state_manager.current_state.entity_tracker.last_turn_end_entity
        entity = self.rg.get_recommended_entity(state)
        if entity != last_entity:
            raise CantRespondError("Recommended entity changed from last turn")
        if self.is_no(utterance):
            state.entity_state[entity.name].finished_talking = True
            conditional_state = ConditionalState(responding_treelet=self.__repr__())
            return ResponseGeneratorResult(text=self.rg.state_manager.current_state.choose_least_repetitive(HANDOVER_TEXTS),
                                           priority=ResponsePriority.STRONG_CONTINUE,
                                           needs_prompt=True,
                                           state=state,
                                           cur_entity=None,
                                           conditional_state=conditional_state)
        elif self.is_yes(utterance):
            conditional_state = ConditionalState(
                cur_doc_title=entity.name,
                responding_treelet=self.__repr__())

            return ResponseGeneratorResult(text=self.rg.state_manager.current_state.choose_least_repetitive(AGREED),
                                           priority=ResponsePriority.STRONG_CONTINUE,
                                           needs_prompt=True,
                                           state=state,
                                           cur_entity=entity,
                                           conditional_state=conditional_state)

        else:
            # Ambiguous case
            state.entity_state[entity.name].finished_talking = True
            conditional_state = ConditionalState(responding_treelet=self.__repr__())
            return ResponseGeneratorResult(text=self.rg.state_manager.current_state.choose_least_repetitive(ABMIGUOUS),
                                           priority=ResponsePriority.STRONG_CONTINUE,
                                           needs_prompt=True,
                                           state=state,
                                           cur_entity=None,
                                           conditional_state=conditional_state)

    @measure
    def get_can_start_response(self, state : State) -> ResponseGeneratorResult:
        entity = self.rg.get_recommended_entity(state)
        if entity:
            raise CantRespondError(f"cur_entity {entity} has been set. Will not try to introduce a previously user mentioned untalked entity")
        latest_untalked_entity, text, conditional_state = self.introduce_entity(state)
        return ResponseGeneratorResult(text=text,
                                       priority=ResponsePriority.CAN_START,
                                       needs_prompt=False,
                                       state=state,
                                       cur_entity=latest_untalked_entity,
                                       conditional_state=conditional_state)

    @measure
    def get_prompt(self, state: State, force_start=False) -> PromptResult:
        if force_start:
            latest_untalked_entity, text, conditional_state = self.introduce_entity(state, force_start)
            return PromptResult(text=text,
                                prompt_type=PromptType.FORCE_START,
                                state=state,
                                cur_entity=latest_untalked_entity,
                                conditional_state=conditional_state)

        entity = self.rg.get_recommended_entity(state)
        if entity:
            raise CantRespondError(f"cur_entity {entity} has been set. Will not try to introduce a previously user mentioned untalked entity")
        latest_untalked_entity, text, conditional_state = self.introduce_entity(state)
        return PromptResult(text=text,
                            prompt_type=PromptType.CONTEXTUAL,
                            state=state,
                            cur_entity=latest_untalked_entity,
                            conditional_state=conditional_state)

