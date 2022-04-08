from enum import Enum
import logging
import jsonpickle
from typing import List, Optional, Union, Set
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity, EntityLinkerResult
from chirpy.core.latency import measure
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, UpdateEntity, AnswerType
from chirpy.core.entity_linker.thresholds import SCORE_THRESHOLD_NAV_ABOUT, SCORE_THRESHOLD_NAV_NOT_ABOUT, SCORE_THRESHOLD_EXPECTEDTYPE
from chirpy.core.entity_linker.entity_groups import EntityGroup

logger = logging.getLogger('chirpylogger')

class TransitionType(Enum):
    POSNAV = 1                      # explicit positive navigation
    RESPONSE_TO_QUESTION = 2
    CHANGE_TOPIC = 3
    IN_CONTEXT = 4

class EntityTrackerState(object):
    """
    Tracks the status of which entities we're talking about, have finished talking about, and which to talk about next.
    """

    def __init__(self):
        self.cur_entity = None  # the current entity under discussion (can be None)
        self.talked_rejected = []  # entities we talked about in the past, and stopped talking about because the user indicated they didn't want to talk about it any more
        self.talked_finished = []  # entities we talked about in the past, that aren't in talked_rejected
        self.talked_transitionable = []
        self.transitional_entity = None
        self.user_mentioned_untalked = []  # entities the user mentioned (in high_prec set) that have not yet been the cur_entity
        self.expected_type = None  # the expected EntityType of the next user utterance
        self.user_topic_unfound = None  # On turns when the user requested a topic but we were unable to link to it, we set this to the topic (str)
        self.is_personal_posnav = False # If the user requested posnav for a personal entity (e.g. "my girlfriend")

        # history is a list of dictionaries. each dictionary corresponds to one turn and has keys 'user', 'response',
        # and sometimes 'prompt'. The values are the cur_entity (WikiEntity or None) after each of those rounds
        # within one turn.
        self.history = []

    def init_for_new_turn(self):
        """Prepare the EntityTrackerState for a new turn"""
        self.history.append({})
        self.user_topic_unfound = None

    def cur_entity_initiated_by_user_this_turn(self, current_state) -> bool:
        """
        Returns True iff the cur_entity is not None, AND it was initiated by the user on the current turn.
        "Initiated by the user on the current turn" means that:
            - the current cur_entity was not cur_entity at the end of the last turn, AND
            - cur_entity is among the EntityLinkerResults for this turn (i.e. was mentioned by the user on this turn)
        """
        # Get entity linker output
        if not hasattr(current_state, 'entity_linker'):
            logger.error('No entity_linker in current_state. This should have been caught and fixed by the NLP '
                         'pipeline. Setting entity_linker to empty EntityLinkerResult in current_state.')
            current_state.entity_linker = EntityLinkerResult()
        entity_linker_result = current_state.entity_linker

        return self.entity_initiated_on_turn


    @property
    def last_turn_end_entity(self) -> Optional[WikiEntity]:
        """
        Returns what the cur_entity was at the end of the previous turn (i.e. the cur_entity given by the prompting RG,
        if there was one, otherwise the cur_entity given by the responding RG). If there was no last turn, returns None.
        """
        # We assume init_for_new_turn() has already run for this turn
        if len(self.history) == 0:
            raise ValueError("history has length 0")
        elif len(self.history) == 1:
            return None  # this is first turn
        else:
            last_turn = self.history[-2]
            if 'prompt' in last_turn:
                return last_turn['prompt']
            else:
                return last_turn['response']

    @property
    def recommended(self) -> List[WikiEntity]:
        """Returns a list of Entities we haven't talked about, that are recommended to talk about"""
        # For now we just return the untalked entities that the user has mentioned in the past.
        # In the future, we might add the ability to identify entities relating to the user's interests
        return self.user_mentioned_untalked

    def talked(self, entity: WikiEntity) -> bool:
        """
        Returns True if we are currently, or have previously, discussed this WikiEntity.
        """
        return entity == self.cur_entity or entity in self.talked_rejected or entity in self.talked_finished

    def finish_entity(self, entity: Optional[WikiEntity], transition_is_possible=True):
        """If entity is not None, put it on self.talked_finished"""
        
        if entity is not None and not isinstance(entity, WikiEntity):
            logger.error(f"This is an error. This should be a WikiEntity object but {entity} is of type {type(entity)}")
            entity = None

        if entity is not None and entity not in self.talked_finished:
            logger.info(f'Putting entity {entity} on the talked_finished list')
            self.talked_finished.append(entity)

        if entity is not None and transition_is_possible:
            self.talked_transitionable.append(entity)

        if not transition_is_possible and entity in self.talked_transitionable:
            self.talked_transitionable = [x for x in self.talked_transitionable if x is not entity]

    def reject_entity(self, entity: Optional[WikiEntity]):
        """If entity is not None, put it on self.talked_rejected"""
        if entity is not None and entity not in self.talked_rejected:
            logger.info(f'Putting entity {entity} on the talked_rejected list')
            self.talked_rejected.append(entity)

    def get_negnav_entities(self, nav_intent_output, entity_linker_result) -> Set[WikiEntity]:
        """
        Get a list of WikiEntities that the user is rejecting via negative navigational intent.
        """
        if not nav_intent_output.neg_intent:
            return set()

        # If there's negnav intent, reject cur_entity and any entities that can be detected in the topic slot
        # (if a topic slot was supplied)
        negnav_entities = {self.cur_entity} if self.cur_entity is not None else set()
        if nav_intent_output.neg_topic_is_supplied:
            (neg_topic_span, neg_about_keyword) = nav_intent_output.neg_topic
            score_threshold = SCORE_THRESHOLD_NAV_ABOUT if neg_about_keyword else SCORE_THRESHOLD_NAV_NOT_ABOUT

            # Construct a condition fn to only return True when the entity is in the neg_topic_span and has score above score_threshold
            def condition_fn(entity_linker_result, linked_span, entity) -> bool:
                return linked_span.span in neg_topic_span and entity.confidence >= score_threshold

            negnav_slot_entity = entity_linker_result.top_ent(condition_fn)
            if negnav_slot_entity:
                negnav_entities.add(negnav_slot_entity)
        else:
            neg_topic_span = None

        logger.primary_info(f"User expressed NegativeNavigational intent with topic slot='{neg_topic_span}', when "
                            f"cur_entity={self.cur_entity}, so we've identified these entities as negative: {negnav_entities}")
        return negnav_entities


    def get_new_ent_from_posnav(self, nav_intent_output, entity_linker_result) -> Optional[WikiEntity]:
        """
        Assuming the user has expressed positive navigational intent, identify the new cur_entity.
        """
        assert nav_intent_output.pos_intent

        # If the user is saying "I want to talk about the current topic" then keep the same cur_entity
        if nav_intent_output.pos_topic_is_current_topic:
            logger.primary_info(f"User has PositiveNavigational intent for the current topic, so keeping the same cur_entity")
            return self.cur_entity

        # If the user is saying "I want to talk about..." then set cur_entity to None
        elif nav_intent_output.pos_topic_is_hesitate or nav_intent_output.pos_topic is None:
            logger.primary_info(f"User has PositiveNavigational intent but didn't supply a topic, so setting cur_entity to None")
            return None

        # Otherwise, the user has specified a topic ("I want to talk about X").
        # Find the highest-priority entity in that slot, which is a top ent in the high prec set, or a manual link,
        # or has score above a threshold (which is lower than the entity linker's usual high-prec threshold).
        else:
            assert nav_intent_output.pos_topic_is_supplied
            (pos_topic_span, pos_about_keyword) = nav_intent_output.pos_topic
            score_threshold = SCORE_THRESHOLD_NAV_ABOUT if pos_about_keyword else SCORE_THRESHOLD_NAV_NOT_ABOUT
            logger.primary_info(f"User has PositiveNavigational intent with topic_span='{pos_topic_span}' and "
                                f"about_keyword={pos_about_keyword}, so looking for entities in '{pos_topic_span}' "
                                f"that are a top ent in the high prec set, or a manual link, or have score over {score_threshold}")

            if 'my' in pos_topic_span.split():
                logger.primary_info("Pos topic span has `my` in it; don't link (but set IsPersonalPosNav to True).")
                self.is_personal_posnav = True
                return None

            # Construct a condition fn to filter for only the entities we want
            def condition_fn(entity_linker_result, linked_span, entity) -> bool:
                if linked_span.span not in pos_topic_span:
                    return False
                if entity == linked_span.top_ent and linked_span in entity_linker_result.high_prec:
                    return True
                if entity == linked_span.manual_top_ent:
                    return True
                if entity.confidence >= score_threshold:
                    return True
                return False

            top_ent = entity_linker_result.top_ent(condition_fn)

            if top_ent:
                logger.primary_info(f"Identified {top_ent} as the new cur_entity (from user's PosNav slot)")
                return top_ent
            else:
                logger.primary_info(f'User asked to talk about topic "{pos_topic_span}" but we were unable to link to '
                                    f'it, so setting cur_entity=None and setting self.user_topic_unfound="{pos_topic_span}"')
                self.user_topic_unfound = pos_topic_span  # note that we failed to link this topic
                return None

    @measure
    def update_from_user(self, state_manager):
        """
        Update at the start of the turn, after running NLP pipeline but before running RGs.

        Inputs:
            current_state: the overall State of the bot, after running NLP pipeline but before running RGs
        """
        # import pdb; pdb.set_trace()
        current_state = state_manager.current_state
        # Get entity linker output
        if not hasattr(current_state, 'entity_linker'):
            logger.error('No entity_linker in current_state. This should have been caught and fixed by the NLP '
                         'pipeline. Setting entity_linker to empty EntityLinkerResult in current_state.')
            current_state.entity_linker = EntityLinkerResult()


        entity_linker_result = current_state.entity_linker
        nav_intent_output = current_state.navigational_intent
        logger.primary_info(f'Updating the EntityTrackerState: {self}\nafter user utterance: '
                            f'"{current_state.text}"\nwith linked entities: {entity_linker_result}'
                            f'\nwith navigational intent output: {nav_intent_output}')

        # import pdb; pdb.set_trace()

        self.entity_initiated_on_turn = None
        self.is_personal_posnav = False

        negnav_entities = self.get_negnav_entities(nav_intent_output, entity_linker_result)

        if nav_intent_output.pos_intent:
            self.entity_initiated_on_turn = self.get_new_ent_from_posnav(nav_intent_output, entity_linker_result)
        if nav_intent_output.neg_intent:
            for negnav_entity in self.get_negnav_entities(nav_intent_output, entity_linker_result):
                self.reject_entity(negnav_entity)

        # Otherwise, get the highest-priority WikiEntity that satisfies (a) AND (b):
        # (a) is not in negnav_entities, or in a LinkedSpan which contains any negnav_entity as an candidate entity
        # (b) is top entity for a LinkedSpan in the entity-linker's high precision set, OR is a manual link, OR is of expected_type with score above SCORE_THRESHOLD_EXPECTEDTYPE (if expected_type is specified)
        def condition_fn(entity_linker_result, linked_span, entity) -> bool:
            if entity in negnav_entities or any(negnav_entity in linked_span.entname2ent.values() for negnav_entity in negnav_entities):
                return False
            if entity == linked_span.top_ent and linked_span in entity_linker_result.high_prec:
                return True
            if entity == linked_span.manual_top_ent:
                return True
            if self.expected_type is not None and self.expected_type.matches(entity) and entity.confidence >= SCORE_THRESHOLD_EXPECTEDTYPE:
                return True
            return False


        last_response = state_manager.last_state_response
        last_answer_type = last_response.answer_type if last_response else None

        logger.primary_info(f"Last response is {last_response}; last answer type is {last_answer_type}; options are [{AnswerType.QUESTION_SELFHANDLING}, {AnswerType.QUESTION_HANDOFF}]")

        # Do we expect to initiate a new entity on this turn?
        if self.entity_initiated_on_turn is None and last_answer_type in [AnswerType.QUESTION_SELFHANDLING, AnswerType.QUESTION_HANDOFF]:
            logger.primary_info(f"Searching for highest-priority entity that (a) isn't in negnav_entities={negnav_entities} or in a LinkedSpan that contains any negnav_entity, "
                                f"and (b) is a top ent in high-prec set, or is a manual link" + (f", or matches expected_type='{self.expected_type}' and score "
                                f"over {SCORE_THRESHOLD_EXPECTEDTYPE}" if self.expected_type else ''))
            self.entity_initiated_on_turn = entity_linker_result.top_ent(condition_fn)  # WikiEntity or None
            if self.entity_initiated_on_turn is not None:
                logger.primary_info(f"Got a new cur_entity")
            else:
                logger.primary_info(f"Got no new cur_entity")

            if self.entity_initiated_on_turn != self.cur_entity and self.cur_entity is not None:
                if self.cur_entity not in negnav_entities:
                    self.finish_entity(self.cur_entity)   # move to talked_finished
                # Remove new_entity from user_mentioned_untalked
                if self.entity_initiated_on_turn in self.user_mentioned_untalked:
                    logger.primary_info(f'Removing {self.entity_initiated_on_turn} from {self.user_mentioned_untalked}')
                    self.user_mentioned_untalked = [e for e in self.user_mentioned_untalked if e != self.entity_initiated_on_turn]



        if nav_intent_output.neg_intent or nav_intent_output.pos_intent or last_answer_type in [AnswerType.QUESTION_SELFHANDLING, AnswerType.QUESTION_HANDOFF]:
            self.cur_entity = self.entity_initiated_on_turn

        for linked_span in current_state.entity_linker.high_prec:
            if not self.talked(linked_span.top_ent):
                logger.info(f'Adding {linked_span.top_ent} to user_mentioned_untalked')
                self.user_mentioned_untalked.append(linked_span.top_ent)

        logger.primary_info(f'The EntityTrackerState is now: {self}')

        # Update the entity tracker history
        self.history[-1]['user'] = self.cur_entity

    def record_untalked_high_prec_entities(self, current_state):
        """
        Take any entities in the entity linker's high precision set for this turn, and if they haven't been discussed,
        put them in user_mentioned_untalked.
        """
        # Get entity linker output
        if not hasattr(current_state, 'entity_linker'):
            logger.error('No entity_linker in current_state. This should have been caught and fixed by the NLP '
                         'pipeline. Setting entity_linker to empty EntityLinkerResult in current_state.')
            current_state.entity_linker = EntityLinkerResult()
        entity_linker_result = current_state.entity_linker

        # Put any undiscussed high_prec entities in user_mentioned_untalked
        for ls in entity_linker_result.high_prec:
            if not self.talked(ls.top_ent):
                logger.info(f'Adding {ls.top_ent} to user_mentioned_untalked')
                self.user_mentioned_untalked.append(ls.top_ent)

    def update_from_rg(self, result: Union[ResponseGeneratorResult, PromptResult, UpdateEntity], rg: str, current_state):
        """
        Update after receiving the output of a RG's get_response/get_prompt/get_entity fn.

        Inputs:
            result: ResponseGeneratorResult, PromptResult, or UpdateEntity
            rg: the name of the RG that provided the new entity
        """
        if isinstance(result, UpdateEntity):
            new_entity = result.cur_entity
            phase = 'get_entity'
        else:
            phase = 'response' if isinstance(result, ResponseGeneratorResult) else 'prompt'
            new_entity = result.cur_entity  # WikiEntity or None
            self.expected_type = result.expected_type  # EntityGroup or None. expected type for the next user utterance.
            if self.expected_type:
                logger.info(f'Setting self.expected_type to "{self.expected_type}" based on {rg} RG {phase} result')

        transition_is_possible = not getattr(result, 'no_transition', False)

        if new_entity == self.cur_entity:
            logger.primary_info(f'new_entity={new_entity} from {rg} RG {phase} is the same as cur_entity, so keeping EntityTrackerState the same')
        else:
            if phase == 'response' and transition_is_possible and self.cur_entity is not None and new_entity is None:
                self.transitional_entity = self.cur_entity
            else:
                self.transitional_entity = None
            logger.primary_info(f"In phase {phase}, transitional entity is {self.transitional_entity}")
            if rg == 'TRANSITION' and phase == 'response':
                self.reject_entity(self.cur_entity)
            else:
                self.finish_entity(self.cur_entity, transition_is_possible)
            self.cur_entity = new_entity
            # Remove new_entity from user_mentioned_untalked
            if new_entity in self.user_mentioned_untalked:
                logger.primary_info(f'Removing {new_entity} from {self.user_mentioned_untalked}')
                self.user_mentioned_untalked = [e for e in self.user_mentioned_untalked if e != new_entity]

            logger.primary_info(f'Set cur_entity to new_entity={new_entity} from {rg} RG {phase}')
        logger.primary_info(f'EntityTrackerState after updating wrt {rg} RG {phase}: {self}')

        # If we're updating after receiving UpdateEntity from an RG, put any undiscussed high precision entities that
        # the user mentioned this turn in user_mentioned_untalked
        if isinstance(result, UpdateEntity):
            self.record_untalked_high_prec_entities(current_state)

        # Update the entity tracker history
        if phase == 'get_entity':
            self.history[-1]['user'] = self.cur_entity
        else:
            self.history[-1][phase] = self.cur_entity

    def __repr__(self, show_history=False):
        output = f"<EntityTrackerState: "
        output += f"cur_entity={self.cur_entity.name if self.cur_entity else self.cur_entity}"
        output += f", talked_finished={[ent.name for ent in self.talked_finished]}"
        output += f", talked_rejected={[ent.name for ent in self.talked_rejected]}"
        output += f", talked_transitionable={[ent.name for ent in self.talked_transitionable]}"
        output += f", transitional_entity={self.transitional_entity}"
        output += f", user_mentioned_untalked={[ent.name for ent in self.user_mentioned_untalked]}"
        output += f", is_personal_posnav={self.is_personal_posnav}"
        if show_history:
            output += f", history={self.history}"
        output += '>'
        return output

    def restrict_entities(self, entities: List[WikiEntity]):
        """
        Restrict the contents of this EntityTrackerState to only contain the entities in entities.
        Note, this will *not* delete the cur_entity, even if it's not in entities.
        """
        def keep_entity(ent: Optional[WikiEntity]) -> bool:
            if ent is None:
                return True
            return ent in entities
        self.talked_finished = [ent for ent in self.talked_finished if keep_entity(ent)]
        self.talked_rejected = [ent for ent in self.talked_rejected if keep_entity(ent)]
        self.user_mentioned_untalked = [ent for ent in self.user_mentioned_untalked if keep_entity(ent)]
        self.history = [{k: ent for k, ent in turn.items() if keep_entity(ent)} for turn in self.history]

    @measure
    def reduce_size(self, max_size: int):
        """Return a version of this EntityTrackerState which, when jsonpickled, is under max_size"""
        logger.info(f'Attempting to reduce size of EntityTrackerState to less than {max_size}:\n{self.__repr__(show_history=True)}')

        # Make a set (no duplicates) of all the WikiEntities stored in this EntityTrackerState
        entity_set = set()
        entity_set.add(self.cur_entity)
        entity_set.update(self.talked_finished)
        entity_set.update(self.talked_rejected)
        entity_set.update(self.user_mentioned_untalked)
        entity_set.update({ent for turn in self.history for ent in turn.values()})
        if None in entity_set:
            entity_set.remove(None)

        # Ensure that all WikiEntities stored in this EntityTrackerState point to the version in entity_set
        entname2ent = {ent.name: ent for ent in entity_set}
        def replace_ent(ent: Optional[WikiEntity]):
            """Returns the version of ent that's in entity_set"""
            if ent is None:
                return None
            return entname2ent[ent.name]
        self.cur_entity = replace_ent(self.cur_entity)
        self.talked_finished = [replace_ent(ent) for ent in self.talked_finished]
        self.talked_rejected = [replace_ent(ent) for ent in self.talked_rejected]
        self.user_mentioned_untalked = [replace_ent(ent) for ent in self.user_mentioned_untalked]
        self.history = [{k: replace_ent(ent) for k, ent in turn.items()} for turn in self.history]

        # Check size
        encoded_result = jsonpickle.encode(self)
        logger.info(f'After de-duplicating WikiEntities (there are now {len(entity_set)} unique WikiEntities: {entity_set}), '
                    f'EntityTrackerState size={len(encoded_result)}:\n{self.__repr__(show_history=True)}')
        if len(encoded_result) < max_size:
            return

        # If still too big, remove oldest WikiEntities until it's small enough
        MAX_ENTITITES = 10

        def most_recent_turn(ent: WikiEntity) -> int:
            """
            Returns the most recent turn on which this entity was discussed. If the entity is not in the history,
            returns -1.
            """
            for turn_num in range(len(self.history)-1, -1, -1):
                if ent in self.history[turn_num].values():
                    return turn_num
            return -1

        # Order the entities by when they were most recently discussed, most recent first
        entities_chronological = sorted(list(entity_set), key=lambda ent: most_recent_turn(ent), reverse=True)
        logger.info(f'entities_chronological (most recent first): {entities_chronological}')

        # Remove oldest WikiEntities until it's small enough
        while len(encoded_result) >= max_size:

            # Reduce to most recent MAX_ENTITIES. After that, remove oldest entities one by one
            if len(entities_chronological) > MAX_ENTITITES:
                entities_chronological = entities_chronological[:MAX_ENTITITES]
            elif len(entities_chronological) > 0:
                entities_chronological = entities_chronological[:-1]
            else:
                logger.error(f'EntityTrackerState only contains the cur_entity={self.cur_entity}, which has size '
                             f'{len(jsonpickle.encode(self.cur_entity))}, and EntityTrackerState is still too large '
                             f'with size {len(encoded_result)}:\n{self.__repr__(show_history=True)}')
                return

            # Restrict EntityTrackerState's contents to entities_chronological
            self.restrict_entities(entities_chronological)

            # Check size
            encoded_result = jsonpickle.encode(self)
            logger.info(f'After restricting history to most recent {len(entities_chronological)} WikiEntities: {entities_chronological}, '
                        f'EntityTrackerState size={len(encoded_result)}:\n{self.__repr__(show_history=True)}')



def test_entity_tracker(user_utterance, bot_utterance='', expected_type=None):
    """Convenience function for testing the entity tracker. Not used in the actual bot; just for development."""
    from chirpy.annotators.navigational_intent.navigational_intent import get_nav_intent
    from chirpy.core.entity_linker.entity_linker import entity_link
    from chirpy.core.asr.index_phone_to_ent import MockG2p

    class State(object):
        def __init__(self, text, history):
            self.text = text
            self.history = history

    current_state = State(user_utterance, [bot_utterance])

    # Run nav intent
    current_state.navigational_intent = get_nav_intent(user_utterance, current_state.history)

    # Run entity linker
    mock_g2p_module = MockG2p()
    corenlp = None
    current_state.entity_linker = entity_link(user_utterance, corenlp, mock_g2p_module, include_common_phrases=(expected_type is not None), expected_type=expected_type)

    # Run entity tracker
    current_state.entity_tracker = EntityTrackerState()
    current_state.entity_tracker.init_for_new_turn()
    current_state.entity_tracker.expected_type = expected_type
    current_state.entity_tracker.update_from_user(current_state)

    return current_state



def main():

    from chirpy.core.logging_utils import setup_logger, LoggerSettings
    from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE, EntityGroup

    # Setup logging
    LOGTOSCREEN_LEVEL = logging.DEBUG
    logger_settings = LoggerSettings(logtoscreen_level=LOGTOSCREEN_LEVEL, logtoscreen_usecolor=True,
                                     logtofile_level=None, logtofile_path=None,
                                     logtoscreen_allow_multiline=True, integ_test=False, remove_root_handlers=False)
    setup_logger(logger_settings)

    # Test
    bot_utterance = ''
    user_utterance = "florida"
    expected_type = ENTITY_GROUPS_FOR_EXPECTED_TYPE.location_related
    test_entity_tracker(user_utterance, bot_utterance, expected_type)



if __name__ == "__main__":
    main()
