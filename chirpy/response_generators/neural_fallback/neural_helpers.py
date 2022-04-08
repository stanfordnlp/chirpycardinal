"""
This file contains helper functions for using neural response generators. Which currently include
* Apply various kinds of filtering
* Get a random fallback prompt for a given state
"""
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.core.util import contains_phrase, filter_and_log
import random
import logging
from functools import lru_cache
from typing import List, Tuple, Optional
from concurrent import futures
logger = logging.getLogger('chirpylogger')


# Phrases we want to ban from neural responses e.g. because we don't want to give advice, say that people "should" do things, seem over-confident, etc
ADVICE_PHRASES = set(['should', "why don't you", 'you can', "i'm sure", "i am sure"])

# This flag determines whether we use neural fallback for handoff phrases (e.g. to replace "OK, cool!" with needs_prompt=True)
# This flag doesn't affect the NeuralFallback RG
# If this flag is True, you need to make sure a neural module is in the NLP pipeline.
USE_NEURAL_FALLBACK_FOR_HANDOFF = False
NEURAL_DECODE_CONFIG = {
    'temperature': 0.7,
    'top_k': 5,
    'top_p': 0.9,
    'min_length': 5
}

BLACKLIST = ['my child', 'my parent', 'my father', 'my mother', 'my wife', 'my husband', 'my daughter', 'my son',
             'my family', 'my cat', 'my dog', 'my car', 'my job', 'i\'ve been studying', 'i\'m a', 'i work', 'i study',
             'i am', 'i live', 'i drive',  'i\'m going to go', 'i\'m going to visit', 'mall', 'woman', 'women', 'man', 'did you know',

             'girl', 'boy', 'african', 'european', 'asian', 'american', 'hookie', 'chevy', 'ford', 'toyota', 'honda', 'overrated',
             'co-worker', 'i live',
             'do for you', 'do your family', 'talk to your family', 'good friends', 'any friends', 'friend of mine',
             'you\'re not a' # 'you're not a friend of mine'
             ]

def contains_advice(response):
    return contains_phrase(response, ADVICE_PHRASES, 'Eliminating neural response "{}" because it contains bad phrase "{}"')

def neural_response_filtering(responses: List[Tuple[str]], scores: Optional[List[Tuple[float]]] = None):
    """
    Takes in a list of responses and applies basic filtering which includes
    * removing duplicates
    * removing offensive responses
    * removing advice

    Note that this function is a wrapper around _basic_filtering where the above filtering takes place.
    In this function the input is converted to a Tuple[str] to be able to hash and cache
    Args:
        responses (List[str]): each string is a possible response paired with its neural-model conditional likelihood

    Returns:
        List[str]: Each string is a filtered possible response
    """

    # Need to convert to tuple to be able to hash for the cache
    responses, scores = _neural_response_filtering(tuple(responses), tuple(scores))
    return responses, scores

@lru_cache(maxsize=128)
def _neural_response_filtering(responses: Tuple[str], scores: Tuple[float]):
    """
    The function where actual filtering logic takes place for basic filtering
    Args:
        responses (List[str]): each string is a possible response

    Returns:
        List[str]: Each string is a filtered possible response
    """

    response_score_pairs = list(zip(responses, scores))
    # remove duplicates
    response_score_pairs = list(set(response_score_pairs))

    # remove offensive
    response_score_pairs = filter_and_log(lambda r: not contains_offensive(r[0]), response_score_pairs,
                            'neural_responses', 'they contain offensive phrases')

    # remove advice
    response_score_pairs = filter_and_log(lambda r: not contains_advice(r[0]), response_score_pairs,
                            'neural_responses', 'they contain advice')
    if len(response_score_pairs):
        return list(zip(*response_score_pairs))
    else:
        return tuple(), tuple()

def get_permissible_fallback_neural_responses(current_state) -> List[str]:
    try:
        # TODO: Should check if hasattr(current_state, 'blenderbot')
        if isinstance(current_state.blenderbot, futures.Future):
            future_result = current_state.blenderbot.result()
            setattr(current_state, 'blenderbot', future_result)
        responses, scores = current_state.blenderbot
        responses, scores = neural_response_filtering(responses, scores)

        # remove questions
        responses = filter_and_log(lambda r: '?' not in r[0], responses, 'neural_responses', 'they are questions')

        return responses
    except Exception:
        logger.error("Exception occurred while getting a random fallback neural response", exc_info=True)
        return None

def get_random_fallback_neural_response(current_state)->Optional[str]:
    """
    DON'T CALL THIS FN DIRECTLY TO USE AS A HANDOFF PHRASE (i.e. with needs_prompt=True).
    FOR THAT, USE get_neural_fallback_handoff BELOW.

    Get a random neural response appropriate to be used as a fallback.
    These are sentences that are not a question and are not meant to be replied to (hence not used as a prompt).
    We don't believe we have a good way of continuing the conversation if we were to ask an arbitrary question or
    give an arbitrary prompt.
    This filtering ensures that while we acknowledge what the user just said better (by using a neural response),
    we still retain control over the high level direction of the conversation by not giving a neural prompt.

    These are non-offensive, non-advice, non-question neural responses generated by GPT2.

    Args:
        current_state: the current State, which already contains the neural output (because it was run in the NLP
            pipeline)

    Returns:
        str: randomly chosen fallback neural response, or None if there are none
    """
    try:
        if isinstance(current_state.blenderbot, futures.Future):
            future_result = current_state.blenderbot.result()
            setattr(current_state, 'blenderbot', future_result)
        logger.primary_info(f"Current BlenderBot is: {current_state.blenderbot}")
        responses, scores = current_state.blenderbot
        responses, scores = neural_response_filtering(responses, scores)

        # remove questions
        responses = filter_and_log(lambda r: '?' not in r, responses, 'neural_responses', 'they are questions')
        chosen_response = random.choice(responses) if responses else None

        if chosen_response:
            logger.primary_info(f"Chose random neural fallback response {chosen_response}")
        else:
            logger.warning("No fallback neural responses were appropriate")
        return chosen_response
    except Exception:
        logger.error("Exception occurred while getting a random fallback neural response", exc_info=True)
        return None


def get_neural_fallback_handoff(current_state) -> Optional[str]:
    """Get a random neural response to use as a handoff phrase"""
    if USE_NEURAL_FALLBACK_FOR_HANDOFF:
        return get_random_fallback_neural_response(current_state)
    return None
