import logging
import random
from typing import Optional

from chirpy.core.callables import ResponseGenerator
from chirpy.response_generators.acknowledgment.acknowledgments import ACKNOWLEDGMENT_DICTIONARY
from chirpy.response_generators.acknowledgment.state import State, ConditionalState
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_CLASSIFICATION
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import emptyResult, ResponseGeneratorResult
from chirpy.core.response_generator_datatypes import PromptResult, emptyPrompt, UpdateEntity
from chirpy.response_generators.opinion2.opinion_sql import get_opinionable_phrases


logger = logging.getLogger('chirpylogger')


# Get a list of entity names that OPINION has twitter opinions for
opinionable_phrases = get_opinionable_phrases()  # List of "Phrase" object
opinionable_entity_names = {phrase.wiki_entity_name for phrase in opinionable_phrases if phrase.wiki_entity_name}


class AcknowledgmentResponseGenerator(ResponseGenerator):
    """
    A response generator that provides an acknowledgment for the cur_entity, based on the cur_entity's membership
    in certain categories.
    """
    name='ACKNOWLEDGMENT'

    @staticmethod
    def init_state() -> dict:
        return State()

    def get_response(self, state: dict) -> ResponseGeneratorResult:
        current_state = self.state_manager.current_state
        cur_entity = current_state.entity_tracker.cur_entity

        # If the cur_entity isn't a non-None entity initiated by the user on this turn, do nothing
        if not current_state.entity_tracker.cur_entity_initiated_by_user_this_turn(current_state):
            logger.primary_info(f'cur_entity {cur_entity} is not a non-None entity initiated by the user on this turn, so '
                        f'Acknowledgment RG is doing nothing')
            return emptyResult(state)

        # Don't acknowledge entities that OPINION has Twitter opinions on (to avoid contradiction)
        if cur_entity.name in opinionable_entity_names:
            logger.primary_info(f'Opinion RG has Twitter opinions for cur_entity {cur_entity}, so Acknowledgment RG is doing nothing (to avoid contradiction)')
            return emptyResult(state)

        # If we've already acknowledged cur_entity, do nothing
        if cur_entity.name in state.acknowledged:
            logger.primary_info(f'We have already acknowledged cur_entity {cur_entity}, so Acknowledgment RG is doing nothing')
            return emptyResult(state)

        # Go through all possible EntityGroups, from most specific to least specific.
        # For the first one matching cur_entity, that we have acknowledgments for, give the acknowledgment
        for ent_group_name, ent_group in ENTITY_GROUPS_FOR_CLASSIFICATION.ordered_items:
            if ent_group.matches(cur_entity) and ent_group_name in ACKNOWLEDGMENT_DICTIONARY:
                logger.primary_info(f'cur_entity {cur_entity} matches EntityGroup "{ent_group_name}" which we have an acknowledgment for, so giving acknowledgment')
                acknowledgments = [a.format(entity=cur_entity.common_name) for a in ACKNOWLEDGMENT_DICTIONARY[ent_group_name]]
                acknowledgment = self.state_manager.current_state.choose_least_repetitive(acknowledgments)

                # Set priority to FORCE_START if the last active RG was Categories or Fallback (which ask questions that they don't handle), or if the user gave PosNav intent on this turn
                # Otherwise, set priority to CAN_START (so we don't interrupt the active RG's STRONG_CONTINUE)
                if ent_group_name in ['musician', 'musical_group', 'musical_work']:
                    logger.info(f'The best matching group is {ent_group_name}, so Acknowledgment RG is using CAN_START priority to acknowledge cur_entity {cur_entity}')
                    priority = ResponsePriority.CAN_START
                elif self.state_manager.last_state_active_rg in ['CATEGORIES', 'FALLBACK']:
                    logger.info(f'Last active RG was Categories or Fallback, so Acknowledgment RG is using FORCE_START priority to acknowledge cur_entity {cur_entity}')
                    priority = ResponsePriority.FORCE_START
                elif self.state_manager.current_state.navigational_intent.pos_intent:
                    logger.info(f'User has PosNav intent on this turn, so Acknowledgment RG is using FORCE_START priority to acknowledge cur_entity {cur_entity}')
                    priority = ResponsePriority.FORCE_START
                else:
                    logger.info(f"The last active RG is not Categories or Fallback, and the user doesn't have PosNav intent on this turn, so Acknowledgment RG is using CAN_START priority to acknowledge cur_entity {cur_entity}")
                    priority = ResponsePriority.CAN_START

                response = ResponseGeneratorResult(text=acknowledgment, priority=priority, needs_prompt=True, state=state,
                                                   cur_entity=cur_entity, conditional_state=ConditionalState(cur_entity.name))
                return response

        # Return an empty response if all else fails.
        logger.primary_info(f"cur_entity {cur_entity} didn't match any EntityGroups that we have acknolwedgments for, so Acknowledgment RG is giving no response")
        return emptyResult(state)

    @staticmethod
    def get_prompt(state: State) -> PromptResult:
        return emptyPrompt(state)

    @staticmethod
    def get_entity(state: State) -> UpdateEntity:
        return UpdateEntity(False)

    @staticmethod
    def update_state_if_chosen(state: State, conditional_state: Optional[ConditionalState]) -> dict:
        state.update_state_if_chosen(conditional_state)  # this assumes that conditional_state is not None, i.e. when we give a non-empty reponse or prompt we do not set conditional_state to None
        return state

    @staticmethod
    def update_state_if_not_chosen(state: State, conditional_state: Optional[ConditionalState]) -> dict:
        return state  # do nothing
