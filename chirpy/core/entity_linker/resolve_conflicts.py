"""This file contains functions used for resolving conflicting (e.g. nested) LinkedSpans"""

import logging
from typing import Set, Tuple, Optional

from chirpy.core.entity_linker.entity_linker_classes import LinkedSpan
from chirpy.core.util import contains_phrase
from chirpy.core.entity_linker.thresholds import SCORE_THRESHOLD_HIGHPREC, SCORE_THRESHOLD_ELIMINATE_OUTER_SPAN, SCORE_THRESHOLD_CHOOSE_INNER_SPAN_OF_TYPE
from chirpy.core.entity_linker.entity_groups import EntityGroup

logger = logging.getLogger('chirpylogger')


def take_max_score_and_return(linkedspan_to_return, linkedspan_to_eliminate):
    """
    If the two LinkedSpans have the same top-ent, set linkedspan_to_return's top_ent_score to be the max of the two
    top_ent_score, and return linked_span_to_return.
    """
    if linkedspan_to_eliminate.top_ent == linkedspan_to_return.top_ent:
        if linkedspan_to_return.top_ent_score < linkedspan_to_eliminate.top_ent_score:
            logger.info(f'Transferring score of {linkedspan_to_eliminate} to {linkedspan_to_return} as they have the same top_entity')
            linkedspan_to_return.top_ent_score = linkedspan_to_eliminate.top_ent_score
    return set([linkedspan_to_return])


def comparison_fn_nested_spans(linkedspan1: LinkedSpan, linkedspan2: LinkedSpan, expected_type: Optional[EntityGroup]) -> Set[LinkedSpan]:
    """
    If the two linked spans have nested spans, choose which one to keep.
        If they have the same protection level:
            - If the inner LinkedSpan's top_ent is of expected_type, and the outer LinkedSpan's top_ent is not,
                and the inner LinkedSpan has a score above SCORE_THRESHOLD_CHOOSE_INNER_SPAN_OF_TYPE, keep the inner one.
            - If the larger one has a score below SCORE_THRESHOLD_ELIMINATE_OUTER_SPAN, and the inner one has a score above
                SCORE_THRESHOLD_HIGHPREC, keep the inner one.
            - Otherwise, keep the larger one.
        If they have different protection levels, keep the more protected one.
        If the LinkedSpans have the same top_ent, set the surviving LinkedSpan's top_ent_score to be the max of the two.

    Returns:
        set of LinkedSpans to keep
    """
    l1_contains_l2 = contains_phrase(linkedspan1.span, {linkedspan2.span}, '', lowercase_text=False, lowercase_phrases=False, remove_punc_text=False, remove_punc_phrases=False)
    l2_contains_l1 = contains_phrase(linkedspan2.span, {linkedspan1.span}, '', lowercase_text=False, lowercase_phrases=False, remove_punc_text=False, remove_punc_phrases=False)
    if l2_contains_l1 or l1_contains_l2:
        if linkedspan1.protection_level == linkedspan2.protection_level:
            (outer_linkedspan, inner_linkedspan) = (linkedspan2, linkedspan1) if l2_contains_l1 else (linkedspan1, linkedspan2)
            if expected_type is not None:
                if expected_type.matches(inner_linkedspan.top_ent) and not expected_type.matches(outer_linkedspan.top_ent):
                    logger.info(f'Removing {outer_linkedspan} from high prec set because it contains {inner_linkedspan}, '
                                f'the outer one is not of expected_type={expected_type}, the inner one is of expected_type, ')
                    return take_max_score_and_return(inner_linkedspan, outer_linkedspan)
                if expected_type.matches(outer_linkedspan.top_ent) and not expected_type.matches(inner_linkedspan.top_ent):
                    logger.info(f'Removing {inner_linkedspan} from high prec set because it is contained in {outer_linkedspan}, '
                                f'the outer one is of expected_type={expected_type}, the inner one is not of expected_type, ')
                    return take_max_score_and_return(outer_linkedspan, inner_linkedspan)
            if outer_linkedspan.top_ent_score < inner_linkedspan.top_ent_score:
                logger.info(f'Removing {outer_linkedspan} from high prec set because it contains {inner_linkedspan}, '
                            f'the outer one has a score below the inner one')
                return take_max_score_and_return(inner_linkedspan, outer_linkedspan)
            else:
                logger.info(f'Removing {inner_linkedspan} from high prec set because it is nested inside {outer_linkedspan}')
                return take_max_score_and_return(outer_linkedspan, inner_linkedspan)
        elif linkedspan1.protection_level < linkedspan2.protection_level:
            logger.info(f'Removing {linkedspan1} from high prec set because it is nested with more protected {linkedspan2}')
            return take_max_score_and_return(linkedspan2, linkedspan1)
        else:
            logger.info(f'Removing {linkedspan2} from high prec set because it is nested with more protected {linkedspan1}')
            return take_max_score_and_return(linkedspan1, linkedspan2)
    else:
        return set([linkedspan1, linkedspan2])


def comparison_fn_alternative_spans(linkedspan1: LinkedSpan, linkedspan2: LinkedSpan, expected_type: Optional[EntityGroup]) -> Set[LinkedSpan]:
    """
    If the two linked spans are versions of the same original span, choose which one to keep.
        If they have the same protection level:
            If we have an expected_type, only one of them is of expected_type, and that one also has score above SCORE_THRESHOLD_HIGHPREC, choose that one.
            Otherwise, keep the higher-scoring one.
        If they have different protection levels, keep the more protected one

    Returns:
        set of LinkedSpans to keep
    """
    if linkedspan1.span == linkedspan2.span:
        if linkedspan1.protection_level == linkedspan2.protection_level:

            if expected_type is not None:
                linkedspan1_matchestype = expected_type.matches(linkedspan1.top_ent)
                linkedspan2_matchestype = expected_type.matches(linkedspan2.top_ent)
                if linkedspan1_matchestype and not linkedspan2_matchestype and linkedspan1.top_ent_score > SCORE_THRESHOLD_HIGHPREC:
                    logger.info(f'Removing {linkedspan2} from high prec set because it is an alternative form of {linkedspan1}, which is of expected_type and has score over {SCORE_THRESHOLD_HIGHPREC}')
                    return take_max_score_and_return(linkedspan1, linkedspan2)
                elif linkedspan2_matchestype and not linkedspan1_matchestype and linkedspan2.top_ent_score > SCORE_THRESHOLD_HIGHPREC:
                    logger.info(f'Removing {linkedspan1} from high prec set because it is an alternative form of {linkedspan2}, which is of expected_type and has score over {SCORE_THRESHOLD_HIGHPREC}')
                    return take_max_score_and_return(linkedspan2, linkedspan1)

            if linkedspan1.top_ent_score < linkedspan2.top_ent_score:
                logger.info(f'Removing {linkedspan1} from high prec set because it is an alternative form of higher-scoring {linkedspan2}')
                return take_max_score_and_return(linkedspan2, linkedspan1)
            else:
                logger.info(f'Removing {linkedspan2} from high prec set because it is an alternative form of higher-scoring {linkedspan1}')
                return take_max_score_and_return(linkedspan1, linkedspan2)
        elif linkedspan1.protection_level < linkedspan2.protection_level:
            logger.info(f'Removing {linkedspan1} from high prec set because it is an alternative form of more protected {linkedspan2}')
            return take_max_score_and_return(linkedspan2, linkedspan1)
        else:
            logger.info(f'Removing {linkedspan2} from high prec set because it is an alternative form of more protected {linkedspan1}')
            return take_max_score_and_return(linkedspan1, linkedspan2)
    else:
        return set([linkedspan1, linkedspan2])


def resolve_pairwise_conflicts(item_set: Set, comparison_fn) -> Tuple[Set, Set]:
    """
    Applies a pairwise comparison fn to all pairs of items in item_set, and removes those that conflict.

    Inputs:
        item_set: a set of items
        comparison_fn: a function which takes in two items, and returns a set (which could be item1, item2, both or
            neither) of which should be kept
    Returns:
         keep_items: the items that were kept
         removed_items: the items that were removed
    """
    keep_items = set()
    removed_items = set()
    while item_set:
        item1 = item_set.pop()  # remove item1 from item_set
        for item2 in keep_items.union(item_set):  # compare item1 with all other items in keep_items and item_set
            to_keep = comparison_fn(item1, item2)  # set of items

            # If we should remove item1, remove put it in removed_items and break
            if item1 not in to_keep:
                removed_items.add(item1)
                break

            # If we should remove item2, remove it from item_set and put it in removed_items
            if item2 not in to_keep:
                item_set.remove(item2)
                removed_items.add(item2)

        # If we haven't put item1 in remove_items, put it in keep_items
        if item1 not in removed_items:
            keep_items.add(item1)

    return keep_items, removed_items