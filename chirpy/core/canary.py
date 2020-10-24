import logging
import os
import random

logger = logging.getLogger('chirpylogger')

def is_already_canary(event):
    """Returns True iff this event is part of a session that is already a canary session"""
    if 'attributes' in event['session'] and 'canary_session' in event['session']['attributes'] and event['session']['attributes']['canary_session']:
        return True
    return False


def mark_as_canary(event):
    """Marks this event as part of a canary session"""
    if 'attributes' not in event['session']:
        logger.info(f"'attributes' not in event['session']: {event}")
        event['session']['attributes'] = {}
    event['session']['attributes']['canary_session'] = True
    logger.info(f'Marked this event as a canary: {event}')


def should_be_canary(event):
    """Determines whether this turn should be part of canary or not."""
    # If it's already a canary, return True
    if is_already_canary(event):
        return True

    # Get the canary_ratio environment variable.
    canary_ratio = os.environ.get('CANARY_RATIO')
    logger.info(f'canary_ratio is {canary_ratio}')
    if canary_ratio is None:
        return False
    canary_on = os.environ.get('CANARY_ON')
    logger.info(f'canary_on is {canary_on}')
    if canary_on is None:
        return False

    # If this is a new session, randomly decide whether this should be a canary conversation
    if event['session']['new'] and float(canary_ratio) > 0 and random.random() < float(canary_ratio) and canary_on == 'TRUE':
        sessionId = event['session']['sessionId']
        mark_as_canary(event)
        logger.info(f'This session {sessionId} has been assigned to canary test (canary_ratio={canary_ratio})')
        return True

    return False