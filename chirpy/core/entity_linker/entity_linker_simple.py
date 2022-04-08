"""This file contains functions to get the WikiEntity for a *single* span / wiki_name"""

import logging

from typing import Optional

from chirpy.core.entity_linker.entity_linker import link_spans, sort_linked_spans
from chirpy.core.entity_linker.util import add_all_alternative_spans
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity, EntityLinkerResult
from chirpy.core.entity_linker.wiki_data_fetching import get_entities_by_wiki_name
from chirpy.core.entity_linker.entity_groups import EntityGroup
from chirpy.core.latency import measure
from chirpy.core.util import make_text_like_user_text

logger = logging.getLogger('chirpylogger')


@measure
def get_entity_by_wiki_name(wiki_name: str, current_state=None) -> Optional[WikiEntity]:
    """
    Returns the WikiEntity with wiki_name, or None if it can't be found.
    Use this function when you *do* know the official title of the wikipedia article of the entity.
    This fn is *not* case-blind, and wiki_name needs to have the correct capitalization.

    If current_state is supplied, we will first try to save time by searching for the WikiEntity in
    EntityTrackerState/EntityLinkerResults.

    Returns:
        entity: the WikiEntity with name=wiki_name, or None if none could be found
    """

    if not wiki_name:
        return None

    logger.info(f'Getting WikiEntity for wiki_name={wiki_name}')

    if current_state:
        # Try looking in entity tracker state
        entity_tracker_state = current_state.entity_tracker
        if entity_tracker_state:
            for ent in [entity_tracker_state.cur_entity] + entity_tracker_state.talked_rejected + entity_tracker_state.talked_finished + \
                       entity_tracker_state.user_mentioned_untalked + [e for turn in entity_tracker_state.history for e in turn.values()]:
                if ent and ent.name == wiki_name:
                    logger.info(f'Found the entity {ent} with wiki_name="{wiki_name}" in entity_tracker_state')
                    return ent

        # Try looking in entity linker results
        entity_linker_result = current_state.entity_linker
        if entity_linker_result:
            for ls in entity_linker_result.all_linkedspans:
                for ent in ls.entname2ent.values():
                    if ent.name == wiki_name:
                        logger.info(f'Found the entity {ent} with wiki_name="{wiki_name}" in entity_linker_result')
                        return ent

    # Get the entity from our ES index
    entname2ent = get_entities_by_wiki_name([wiki_name])

    # Return
    if wiki_name in entname2ent:
        ent = entname2ent[wiki_name]
        logger.info(f'Got WikiEntity for wiki_name={wiki_name}: {ent}')
        return ent
    else:
        logger.error(f'Unable to get WikiEntity, returning None\n with wiki_name={wiki_name}. ')
        return None


@measure
def link_span_to_entity(span: str, current_state=None, expected_type: Optional[str] = None,
                        must_match_expected_type: bool = True, use_asr_robustness: bool = False) -> Optional[WikiEntity]:
    """
    Attempts to link a single span (this DOES include alternative forms, but DOES NOT include subspans) to an entity.
    Use this function when you *don't* know the official wikipedia article title for the entity - you just have a span
    you're trying to link.

    If expected_type is NOT supplied, we return the top-scoring WikiEntity for this span. If there are no
        WikiEntities, we return None.
    If expected_type IS supplied, we return the top-scoring WikiEntity of expected_type for this span. If there are
        no WikiEntities of expected_type:
            - if must_match_expected_type = True, we return None
            - if must_match_expected_type = False, we return the top-scoring WikiEntity for this span. If there
            are no WikiEntities, we return None.

    Inputs:
        span: the span you want to link
        current_state: Either None or the global bot state. If supplied, we first try to save time by searching through
            EntityLinkerResults for the desired WikiEntity. The result should be the same as if current_state is not
            supplied (but may be faster if you supply current_state).
        expected_type: an EntityGroup representing the group of entities that we expect the result to belong to, or None
        must_match_expected_type: bool; see above
        use_asr_robustness: If True, use ASR robustness in the entity linker (i.e. additionally consider phonetically
            similar entities). This makes the function significantly slower, so only include if spans might contain
            ASR errors. USE_ASR_ROBUSTNESS_OVERALL_FLAG also needs to be True for ASR robustness to be on.

    Returns:
        entity: the best WikiEntity, or None if none could be found
    """
    span = make_text_like_user_text(span)

    assert expected_type is None or isinstance(expected_type, EntityGroup), f"expected_type should be None or EntityGroup, not {type(expected_type)}"

    if not span:
        return None

    if expected_type:
        logger.primary_info(f'Attempting to link span="{span}" to an entity, with use_asr_robustness={use_asr_robustness}, and expected_type={expected_type} and must_match_expected_type={must_match_expected_type}')
    else:
        logger.primary_info(f'Attempting to link span="{span}" to an entity, with use_asr_robustness={use_asr_robustness}')

    # Get the entity_linker_state if supplied
    if current_state:
        entity_linker_result = current_state.entity_linker
    else:
        entity_linker_result = None

    # If entity_linker_result is supplied, see if we have any LinkedSpans whose span matches ours
    if entity_linker_result:
        linked_spans = [ls for ls in entity_linker_result.all_linkedspans if ls.span == span]  # might be empty
    else:
        linked_spans = None

    # If we DON'T have any linked_spans with desired span, run the entity linker on our span
    if not linked_spans:
        spans_to_lookup = {span}

        # Add alternative forms of the span
        spans_to_lookup, altspan2origspan = add_all_alternative_spans(spans_to_lookup, ngrams={span})

        # Link to entities
        linked_spans = link_spans(spans_to_lookup, use_asr_robustness, altspan2origspan, expected_type=expected_type)  # list, might be empty

    # Sort the linked spans by score
    linked_spans = sort_linked_spans(linked_spans)
    logger.info('Linked spans (highest priority first):\n\n{}'.format(
        '\n\n'.join([linked_span.detail_repr for linked_span in linked_spans])))

    # If we got no LinkedSpans, return None
    if not linked_spans:
        logger.primary_info(f'Got no WikiEntities for span="{span}", so returning None')
        return None

    # Take the top entity
    top_ent = linked_spans[0].top_ent

    # If we have no expected_type constraints, return top_ent
    if not expected_type:
        logger.primary_info(f'Linking span="{span}" to top WikiEntity {top_ent}')
        return top_ent

    # Otherwise we have type constraints. Get top WikiEntity of expected_type
    entity_linker_result = EntityLinkerResult([], linked_spans)
    top_ent_of_expected_type = entity_linker_result.best_ent_of_type(expected_type)  # WikiEntity or None

    # If top_ent_of_expected_type is not None, return.
    if top_ent_of_expected_type:
        logger.primary_info(f'Linking span="{span}" to top WikiEntity {top_ent} of type {expected_type}')
        return top_ent_of_expected_type

    # Otherwise top_ent_of_expected_type is None
    else:
        if must_match_expected_type:
            logger.primary_info(f'Got no WikiEntities of type {expected_type} for span="{span}". '
                                f'Because must_match_expected_type=True, returning None')
            return None
        else:
            logger.primary_info(f'Got no WikiEntities of type {expected_type} for span="{span}". Because '
                                f'must_match_expected_type=False, returning top-scoring WikiEntity (not of expected_type): {top_ent}')
            return top_ent



if __name__ == "__main__":
    # You can run this code to try out the entity linking functions

    from chirpy.core.latency import save_latency_plot, clear_events

    # Setup logging with interactive mode logger settings
    from chirpy.core.logging_utils import setup_logger, LoggerSettings

    LOGTOSCREEN_LEVEL = logging.DEBUG
    logger_settings = LoggerSettings(logtoscreen_level=LOGTOSCREEN_LEVEL, logtoscreen_usecolor=True,
                                     logtofile_level=None, logtofile_path=None,
                                     logtoscreen_allow_multiline=True, integ_test=False, remove_root_handlers=False)
    setup_logger(logger_settings)

    # entity = link_span_to_entity('chicago', expected_type=None)  # returns Chicago the city
    # entity = link_span_to_entity('chicago', expected_type='film')  # returns Chicago the movie
    # entity = link_span_to_entity('chicago', expected_type='painting', must_match_expected_type=True)  # returns None
    # entity = link_span_to_entity('chicago', expected_type='painting', must_match_expected_type=False)  # returns Chicago the city

    print(link_span_to_entity('ark: survival evolved'))

    save_latency_plot('entity_linker_latency.png')
