from concurrent import futures
from functools import lru_cache
import logging
import random
import re
from typing import List, Optional, Tuple

from chirpy.core.util import contains_phrase, filter_and_log
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive

from itertools import takewhile

logger = logging.getLogger('chirpylogger')

GPT2ED_DECODE_CONFIG = {
    'do_sample': True,
    #'no_sample': False,
    'min_length': 4,  # in GPT2 tokens
    'max_length': 20,  # in GPT2 tokens
    'temperature': 0.7,
    'top_k': 0,
    'top_p': 0.9,
    'max_history_tokens': 400,  # in GPT2 tokens
    'num_samples': 20,
}

NEURAL_DECODE_CONFIG = { # todo: once all modules are updated to Blenderbot -- no need for janky name converstion code
    'temperature': 0.7,
    'top_k': 5,
    'top_p': 0.9,
}

ADVICE_PHRASES = set(['should', "why don't you", 'you can', "i'm sure", "i am sure"])


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

def is_two_part(response) -> bool:
    """Returns True iff response has at least two parts as indicated by punctuation marks."""
    num_puncs = len([char for char in response if char in ['.', ',', '!', '?']])
    return num_puncs >= 2

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

def is_question(sentence):
    return '?' in sentence or any([sentence.lower().startswith(start)
                                   for start in ['who', 'what', 'when', 'where', 'why', 'how']])

def is_weird(statement):
    statement = statement.lower()

    if any(b in statement for b in BLACKLIST): return True
    return False

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
        current_state: the current State, which already contains the gpt2ed output (because it was run in the NLP
            pipeline)

    Returns:
        str: randomly chosen fallback neural response, or None if there are none
    """
    try:
        logger.primary_info(f"Current neural module state is: {current_state.blenderbot}")
        if isinstance(current_state.blenderbot, futures.Future):
            # Sometimes the call to BlenderBot has not yet finished, in which case we store the future
            # in self.state_manager.current_state.blenderbot and retrieve the result here.
            future_result = current_state.blenderbot.result()
            # Replace the future with the future's result
            setattr(current_state, 'blenderbot', future_result)
        responses, scores = current_state.blenderbot
        responses, scores = neural_response_filtering(responses, scores)

        # remove questions
        if any('?' not in r for r in responses):
            responses = filter_and_log(lambda r: '?' not in r, responses, 'neural_responses', 'they are questions')
        else:
            sentences = [re.split(r"(?<!\w\.\w.)(?<![A-Za-z])(?<=[.?!])\s", response) for response in responses]

            def yeet(s):
                s = s[:2] # no more than 2 sentences
                return " ".join(takewhile(lambda x: not is_question(x), s))

            responses = [yeet(sentence) for sentence in sentences]

            responses = [r for r in responses if len(r.split()) > 3]

        responses = [r for r in responses if not is_weird(r)]
        chosen_response = random.choice(responses) if responses else None

        if chosen_response:
            logger.primary_info(f"Chose random neural fallback response {chosen_response}")
        else:
            logger.warning("No fallback neural responses were appropriate")
        return chosen_response
    except Exception:
        logger.error("Exception occurred while getting a random fallback neural response", exc_info=True)
        return None

def get_neural_fallback_handoff(current_state)->Optional[str]:
    return get_random_fallback_neural_response(current_state)
