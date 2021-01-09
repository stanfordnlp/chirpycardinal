import logging
from typing import Optional
from copy import deepcopy
import random

from chirpy.core.callables import ResponseGenerator
from chirpy.response_generators.neural_helpers import get_neural_fallback_handoff
from chirpy.response_generators.wiki.dtypes import State, CantContinueResponseError, CantRespondError, ConditionalState, \
    CantPromptError
from chirpy.response_generators.wiki.treelets.abstract_treelet import HANDOVER_TEXTS
from chirpy.response_generators.wiki.treelets.convpara_til_treelet import ConvParaTILTreelet
from chirpy.response_generators.wiki.treelets.introduce_entity_treelet import IntroduceEntityTreelet
from chirpy.response_generators.wiki.wiki_utils import token_overlap

from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyResult, emptyPrompt, \
    UpdateEntity
from chirpy.response_generators.wiki.treelets.introductory_treelet import IntroductoryTreelet
from chirpy.response_generators.wiki.treelets.til_treelet import TILTreelet
from chirpy.response_generators.wiki.treelets.handle_section_treelet import HandleSectionTreelet
from chirpy.response_generators.wiki.treelets.open_question_treelet import OpenQuestionTreelet
from difflib import SequenceMatcher
from chirpy.core.smooth_handoffs import SmoothHandoff

CATEGORY_BLACK_LIST = ['Sport', 'Homo sapiens', 'Location (geography)', 'Television', 'Weather', 'Science',
                       'Technology', 'Science, technology, engineering, and mathematics', 'Sex', 'Art', 'Book', ]
ENTITY_BLACK_LIST = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
                     'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                     'November', 'December',
                     'Jews', 'Feces', 'Swine', 'Devil',
                     '2019–20 coronavirus outbreak',
                     'Bible', 'Quran', 'Gospel', 'Christianity' #religious texts
                     'HTTP cookie'
                     ]
logger = logging.getLogger('chirpylogger')

class WikiResponseGenerator(ResponseGenerator):
    name='WIKI'
    def __init__(self, state_manager) -> None:
        super().__init__(state_manager)
        self.all_treelets = {repr(treelet) : treelet for treelet in \
            [IntroductoryTreelet(self), TILTreelet(self), HandleSectionTreelet(self), ConvParaTILTreelet(self),
             OpenQuestionTreelet(self), IntroduceEntityTreelet(self)]}

    def has_overlap_with_history(self, utterance, threshold = 0.5):
        for response_text in self.state_manager.current_state.history:
            percentage_overlap = token_overlap(utterance, response_text)
            if percentage_overlap >= threshold:
                return response_text
        return None

    def remove_overlap(self, old_string: str, new_string: str) -> str:
        """Removes overlapping elements from new string. Returns the longest contiguous substring from the new string. """
        non_overlapping_sequence = ''
        for (tag, i1, i2, j1, j2) in SequenceMatcher(lambda x: x in " \t\n", old_string, new_string).get_opcodes():
            if tag == 'insert' or tag == 'replace':
                if j2-j1 > len(non_overlapping_sequence):
                    non_overlapping_sequence = new_string[j1:j2]
        return non_overlapping_sequence

    def get_recommended_entity(self, state: State):
        recommended_entity = self.state_manager.current_state.entity_tracker.cur_entity
        if recommended_entity:
            if recommended_entity.is_category:
                logger.info(f"Recommended entity {recommended_entity} is a category, not using it for WIKI")
            elif recommended_entity in ENTITY_BLACK_LIST:
                logger.info(f"Recommended entity {recommended_entity} is blacklisted for for WIKI")
            elif recommended_entity.name in state.entity_state and state.entity_state[recommended_entity.name].finished_talking:
                    logger.info(f"Wiki has finished talking about recommended entity {recommended_entity}")
            else:
                return recommended_entity

    def get_untalked_entity(self, state: State):
        untalked_entities = self.state_manager.current_state.entity_tracker.user_mentioned_untalked
        for entity in reversed(untalked_entities):
            if (not entity.is_category) and (not (entity in ENTITY_BLACK_LIST)) and  \
                (not (entity.name in state.entity_state and state.entity_state[entity.name].finished_talking)):
                logger.primary_info(f"Found {entity} in entity_tracker.user_mentioned_untalked, the latest entity"
                                    f"for Wiki to not have finished talking")
                return entity

    def init_state(self) -> State:
        return State()

    def get_entity(self, state:State) -> UpdateEntity:
        prompt_handler = state.prompt_handler.split(":")[0]
        entity = self.get_recommended_entity(state)
        if not entity:
            logger.primary_info("WIKI's get_entity function found no cur_entity and doesn't change the cur_entity either")
            return UpdateEntity(False)
        if (prompt_handler == 'Handle Section Treelet (WIKI)' and
                self.all_treelets['Handle Section Treelet (WIKI)'].any_section_title_matches(state)) or \
            (prompt_handler == 'Open Question Treelet (WIKI)' and
                    len(self.all_treelets['Open Question Treelet (WIKI)'].search_highlights(state))>0):
                return UpdateEntity(True, self.get_recommended_entity(state))

        return UpdateEntity(False)

    def prompted_last_turn(self):
        return self.state_manager.last_state.selected_prompt_rg == 'WIKI'

    def responded_last_turn(self):
        return self.state_manager.last_state.selected_response_rg == 'WIKI'


    def get_response(self, state : State) -> ResponseGeneratorResult:
        """This method will return a response depending on which treelet we are in

        :param state: the current state
        :type state: State
        :return: the result
        :rtype: ResponseGeneratorResult
        """

        # Expected to STRONG_CONTINUE
        base_response = emptyResult(state)
        if self.state_manager.last_state_active_rg == 'WIKI':
            neg_intent = self.state_manager.current_state.navigational_intent.neg_intent  # bool
            if neg_intent:
                logger.primary_info('NavigationalIntent is negative, so doing a hard switch out of WIKI')
                return ResponseGeneratorResult(
                    text=get_neural_fallback_handoff(self.state_manager.current_state) or "Ok, no problem.",
                    priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True, state=state, cur_entity=None,
                    conditional_state=ConditionalState())

        tracked_entity = self.get_recommended_entity(state)
        prompted_options = state.prompted_options
        if self.state_manager.last_state_active_rg == 'WIKI':
            # Should have some idea of how to continue
            # Based on what is in the state, figure out which treelets are applicable for STRONG_CONTINUE
            # If there's a designated continuer, try that, but have a fallback plan
            # Refactor treelets to remove fallbacks from there and have them here centrally
            try:
                logger.info(f"Wiki handing over to prompt handler {state.prompt_handler}.handle_prompt")
                prompt_handler = state.prompt_handler.split(':')[0]
                base_response=self.all_treelets[prompt_handler].handle_prompt(state)
            except CantRespondError:
                logger.info(f"{state.prompt_handler}.handle_prompt return CantRespondError, will try other treelets next")

        state.reset()



        if base_response.priority == ResponsePriority.NO: # No response so far
            # CAN_START
                # Look for entities and how much they've been talked about
                # If it hasn't been talked about, have a sequence of treelets that can check for availability of information
                # try them in sequence
            try:
                base_response = IntroductoryTreelet(self).get_can_start_response(state)
            except CantRespondError:
                try:
                    base_response = OpenQuestionTreelet(self).get_can_start_response(state)
                except CantRespondError:
                    try:
                        if self.state_manager.current_state.experiments.look_up_experiment_value('convpara'):
                            try:
                                base_response = ConvParaTILTreelet(self).get_can_start_response(state)
                            except CantRespondError:
                                base_response = TILTreelet(self).get_can_start_response(state)
                        else:
                            base_response = TILTreelet(self).get_can_start_response(state)
                    except CantRespondError:

                        try:
                            base_response = HandleSectionTreelet(self).get_can_start_response(state)
                        except CantRespondError:
                            try:
                                base_response = IntroduceEntityTreelet(self).get_can_start_response(state)
                            except:
                                if tracked_entity:
                                    logger.primary_info(
                                        f"WIKI has exhausted all treelets for this entity. Handing over with a weak continue.")
                                    apology_text = self.state_manager.current_state.choose_least_repetitive(HANDOVER_TEXTS)
                                    apology_state = deepcopy(state)
                                    apology_state.entity_state[tracked_entity.name].finished_talking = True
                                    apology_response = ResponseGeneratorResult(
                                        text=apology_text,
                                        priority=ResponsePriority.WEAK_CONTINUE,
                                        needs_prompt=True,
                                        cur_entity=None,
                                        state=apology_state,
                                        conditional_state=ConditionalState()
                                    )

                                    return apology_response

        #return base_response
        # If the base response needs a prompt and we have not finished talking about an entity, then get a section prompt
        if base_response.needs_prompt and tracked_entity and not base_response.state.entity_state[tracked_entity.name].finished_talking:
            try:
                # This is a stub for sake of completeness, intro treelet doesn't have ability to continue response
                return IntroductoryTreelet(self).continue_response(base_response)
            except CantContinueResponseError:
                try:
                    return OpenQuestionTreelet(self).continue_response(base_response)
                except CantContinueResponseError:
                    try:
                        if self.state_manager.current_state.experiments.look_up_experiment_value('convpara'):
                            try:
                                return ConvParaTILTreelet(self).continue_response(base_response)
                            except CantContinueResponseError:
                                return TILTreelet(self).continue_response(base_response)
                        else:
                            return TILTreelet(self).continue_response(base_response)
                    except CantContinueResponseError:
                            try:
                                return HandleSectionTreelet(self).continue_response(base_response)
                            except CantContinueResponseError:
                                pass
        return base_response

    def get_prompt(self, state : State) -> PromptResult:
        #try:
        #    return IntroductoryTreelet(self).get_can_start_response(state)
        #except CantRespondError:
        try:
            # If this is a smooth transition from one turn hack on BLM
            if self.state_manager.current_state.smooth_handoff == SmoothHandoff.ONE_TURN_TO_WIKI_GF:
                return IntroduceEntityTreelet(self).get_prompt(state, True)
            else:
                return OpenQuestionTreelet(self).get_prompt(state)
        except CantPromptError:
            try:
                if self.state_manager.current_state.experiments.look_up_experiment_value('convpara'):
                    try:
                        return ConvParaTILTreelet(self).get_prompt(state)
                    except CantRespondError:
                        return TILTreelet(self).get_prompt(state)
                else:
                    return TILTreelet(self).get_prompt(state)
            except CantPromptError:
                try:
                    return HandleSectionTreelet(self).get_prompt(state)
                except CantPromptError:
                    try:
                        return IntroduceEntityTreelet(self).get_prompt(state)
                    except:
                        pass

        return emptyPrompt(state)
        #result = self.all_treelets["Introductory Treelet (WIKI)"].get_prompt(state)

    def update_state_if_chosen(kself, state : State, conditional_state: Optional[ConditionalState]) -> State:
        return state.update(conditional_state)

    def update_state_if_not_chosen(self, state: State, conditional_state: Optional[ConditionalState]) -> State:
        return state

