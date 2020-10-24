import random
from copy import deepcopy
import logging
from typing import Tuple, List, Optional

from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.latency import measure
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult
from chirpy.response_generators.wiki.treelets.abstract_treelet import Treelet
from chirpy.response_generators.wiki.dtypes import State, CantContinueResponseError, CantRespondError, ConditionalState, \
    CantPromptError
import chirpy.response_generators.wiki.wiki_utils as wiki_utils
from chirpy.response_generators.wiki.wiki_utils import token_overlap

logger = logging.getLogger('chirpylogger')

I_LEARNED = ["I read today that {}.",
    "I heard that {}.",
    "I saw online that {}."]
WANNA_KNOW_NEW_ENTITY = ["Wanna know something interesting about {new_entity}?",
                         "Do you have any interest in talking about {new_entity}?",
                         "Let's chat about {new_entity}! What do you say?",
                         "Do you want to chat about {new_entity}?",]
WANNA_KNOW_MORE = ['Wanna know what else is interesting?', 'Wanna know something else?']
CONFIRM2 = ["Would you like to learn more about {} or {}?"]
ACKNOWLEDGE_NO = ['Ok sure.', 'Ok, no problem.', 'For sure.', 'Alright.', 'Of course', 'Sure']

class TILTreelet(Treelet):
    """This treelet is essentially an handle section treelet but we
    respond with a TIL if we have one. If we do, then we allow
    the user to disambiguate between the current document or the
    TIL document. Otherwise we delegate to our super class.

    :param IntroductoryTreelet: Super class that handles regular responses
    :type IntroductoryTreelet: IntroductoryTreelet
    """

    def __repr__(self):
        return "TIL Treelet (WIKI)"

    def __name__(self):
        return "til"

    def get_til(self, entity: str, state: State) -> Optional[Tuple[str, str, str]]:
        """Get a list of TILs that are safe to be served

        :param state: the current state
        :type state: chirpy.response_generators.wiki.dtypes.State
        :param entity: the entity we are getting TIL for
        :type entity: str
        :return: All TIL randomly chosen from a bunch of TILs. Each TIL is of the form (text, doc_title, section_title)
        :rtype: List[Tuple[str, str, str]]

        """
        if entity in state.entity_state and len(state.entity_state[entity].tils_used) >= 2:
            logger.info(f"Already used 2 TILs for f{entity}, not reading out any more")
            return None
        tils = deepcopy(wiki_utils.get_til_title(entity))
        used_tils = state.entity_state[entity].tils_used
        if not tils:
            logger.info(f"Wiki found not TILs for {entity}")
            return None
        overlap_threshold = 0.75
        random.shuffle(tils)
        for til_text, doc_title, section_title in tils:
            overlapping_response = self.rg.has_overlap_with_history(til_text, threshold=overlap_threshold)
            #TODO-future: This should use TFIDF
            overlapping_til = any(token_overlap(til_text, c)>overlap_threshold for c in used_tils)
            if not overlapping_response and not overlapping_til:
                break
        else:
            logger.info("All TILs have either been used, or have a high overlap with previous utterances")
            return None
        return (til_text, doc_title, section_title)

    def respond_til(self, state: State, entity: WikiEntity, til_text: Optional[str]=None) -> ResponseGeneratorResult:
        """This method definitely responds with a TIL if exists and suggest either another
        TIL or sections depending on some heuristics

        :param state: The current state
        :type state: chirpy.response_generators.wiki.dtypes.State
        :param entity: The resolved entity that we are trying to get a TIL for
        :type entity: str
        :return: The response generator result
        :rtype: ResponseGeneratorResult

        """

        if not til_text:
            til_response = self.get_til(entity.name, state)
            if not til_response:
                raise CantRespondError("Not responding with more TILs")
            til_texts, doc_titles, section_titles = til_response
            til_text = self.rg.state_manager.current_state.choose_least_repetitive(I_LEARNED).format(til_texts)

        if til_text[-1] not in ['.', '!', '?']:
            til_text+='.'
        logger.primary_info(f'WIKI is responding with a TIL to entity {entity.name}')
        conditional_state = ConditionalState(
            cur_doc_title=entity.name,
            responding_treelet=self.__repr__(),
            til_used=til_text)
        base_response_result = ResponseGeneratorResult(text=til_text, priority=ResponsePriority.CAN_START,
                                                       needs_prompt=True, state=state, cur_entity=entity,
                                                       conditional_state=conditional_state)
        return base_response_result

    @measure
    def get_prompt(self, state : State) -> PromptResult:
        entity= self.rg.get_recommended_entity(state)
        if not entity:
            raise CantPromptError("No recommended entity")

        til_response = self.get_til(entity.name, state)
        if not til_response:
            raise CantPromptError("Not prompting for more TILs.")

        text = self.rg.state_manager.current_state.choose_least_repetitive(WANNA_KNOW_NEW_ENTITY).format(new_entity=entity.common_name)
        conditional_state = ConditionalState(
            cur_doc_title=entity,
            prompt_handler=self.__repr__(),
            prompted_options=[entity.name]
        )
        if self.rg.state_manager.current_state.entity_tracker.cur_entity == entity:
            prompt_type = PromptType.CURRENT_TOPIC
        else:
            prompt_type = PromptType.CONTEXTUAL
        prompt_result = PromptResult(text=text, prompt_type=prompt_type, state=state, cur_entity=entity,
                                     conditional_state=conditional_state)

        return prompt_result

    @measure
    def continue_response(self, base_response_result: ResponseGeneratorResult) -> ResponseGeneratorResult:
        state = base_response_result.state
        conditional_state = base_response_result.conditional_state
        new_state = state.update(conditional_state)
        entity = base_response_result.cur_entity
        if not entity:
            raise CantContinueResponseError("base_response_result.cur_entity was not set")
        til_response = self.get_til(entity.name, new_state)
        if not til_response:
            raise CantContinueResponseError("Not prompting for more TILs.")

        text = base_response_result.text + ' ' + self.rg.state_manager.current_state.choose_least_repetitive(WANNA_KNOW_MORE)
        conditional_state.prompted_options = [entity.name]
        conditional_state.prompt_handler = self.__repr__()
        base_response_result.conditional_state = conditional_state
        base_response_result.text = text
        base_response_result.needs_prompt = False

        return base_response_result

    @measure
    def handle_prompt(self, state: State):
        utterance = self.rg.state_manager.current_state.text.lower()
        entity = self.rg.get_recommended_entity(state)
        if self.is_yes(utterance) and entity:
            base_response = self.respond_til(state, entity)
            # base_response.text = f"Speaking of {entity.common_name}," + base_response.text
            base_response.priority = ResponsePriority.STRONG_CONTINUE
            return base_response

        elif self.is_no(utterance):
            return ResponseGeneratorResult(text=self.rg.state_manager.current_state.choose_least_repetitive(ACKNOWLEDGE_NO),
                                           priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True, state=state,
                                           cur_entity=None, conditional_state=ConditionalState(
                    responding_treelet=self.__repr__(),

                ))
        raise CantRespondError("couldn't classify user response into YES or NO")

    @measure
    def get_can_start_response(self, state : State) -> ResponseGeneratorResult:
        """This method returns a TIL if we have one and then disambiguate,
        or we delegate to our super class to handle the rest

        :param state: The current state of the RG
        :type state: chirpy.response_generators.wiki.dtypes.State
        :return: the result which we use to utter
        :rtype: ResponseGeneratorResult

        """
        utterance = self.rg.state_manager.current_state.text.lower()
        entity = self.rg.get_recommended_entity(state)
        if not entity:
            raise CantRespondError("No recommended entity")
        base_response =  self.respond_til(state, entity)
        return base_response
