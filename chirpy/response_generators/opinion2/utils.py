from chirpy.core.util import contains_phrase
import os
import csv
import chirpy.response_generators.opinion2.opinion_sql as opinion_sql
from typing import List, Optional, Tuple
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT, NONEMPTY_TEXT, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'user_interest', 'common_solicit_opinion_responses_labeled.csv'), 'r') as f:
    rows = list(csv.reader(f))
    YES = set([utterance for utterance, label, _ in rows if label == 'yes'])
    NO = set([utterance for utterance, label, _ in rows if label == 'no'])
    NEUTRAL = set([utterance for utterance, label, _ in rows if label == 'neutral'])

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'user_interest', 'common_solicit_reason_responses_labeled.csv'), 'r') as f:
    rows = list(csv.reader(f))
    CONTINUE = set([utterance for utterance, label, _ in rows if label == 'continue'])
    EXIT = set([utterance for utterance, label, _ in rows if label == 'exit'])

class LikeRegex(RegexTemplate):
    slots = {
        'adjective': ['really', 'definitely', 'absolutely', 'do'],
        'attitude': ['love', 'like', 'admire', 'adore'],
        'entity': NONEMPTY_TEXT,
        'because': ['because', 'since', 'cause'],
        'reason': OPTIONAL_TEXT,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "i" + " {adjective} {attitude} {entity} {because} {reason}",
        OPTIONAL_TEXT_PRE + "i" + " {attitude} {entity} {because} {reason}",
        OPTIONAL_TEXT_PRE + "i" + " {adjective} {attitude} {entity}",
        OPTIONAL_TEXT_PRE + "i" + " {attitude} {entity}",
        OPTIONAL_TEXT_PRE + "we" + " {adjective} {attitude} {entity} {because} {reason}",
        OPTIONAL_TEXT_PRE + "we" + " {attitude} {entity} {because} {reason}",
        OPTIONAL_TEXT_PRE + "we" + " {adjective} {attitude} {entity}",
        OPTIONAL_TEXT_PRE + "we" + " {attitude} {entity}"
    ]
    positive_examples = [
        ('omg i love cats', {'attitude': 'love', 'entity': 'cats'}),
        ('yeah i definitely like dogs', {'adjective': 'definitely', 'attitude': 'like', 'entity': 'dogs'}),
        ('yes i love cats because they are very quiet', {'attitude': 'love', 'entity': 'cats', 'because': 'because', 'reason': 'they are very quiet'}),
        ('i do like musicals', {'adjective': 'do', 'attitude': 'like', 'entity': 'musicals'})
    ]
    negative_examples = [
        'i hate cats',
        "i don't like cats",
        "i don't really like cats",
        'i\'m not a big fan of dogs',
        'i don\'t really have an opinion',
        'i\'m a big fan of dogs', # This will be caught by sentiment analysis
        'dogs are my favorite animals' # This will be caught by sentiment analysis
    ]

class DislikeRegex(RegexTemplate):
    slots = {
        'attitude': ['hate', 'dislike', 'do not like', 'don\'t like'],
        'entity': NONEMPTY_TEXT,
        'because': ['because', 'since', 'cause'],
        'reason': OPTIONAL_TEXT,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "i" + OPTIONAL_TEXT_MID + "{attitude} {entity} {because} {reason}",
        OPTIONAL_TEXT_PRE + "i" + OPTIONAL_TEXT_MID + "{attitude} {entity}",
        OPTIONAL_TEXT_PRE + "we" + OPTIONAL_TEXT_MID + "{attitude} {entity} {because} {reason}",
        OPTIONAL_TEXT_PRE + "we" + OPTIONAL_TEXT_MID + "{attitude} {entity}",
    ]
    positive_examples = [
        ('omg i hate cats', {'attitude': 'hate', 'entity': 'cats'}),
        ('i definitely don\'t like dogs', {'attitude': 'don\'t like', 'entity': 'dogs'}),
        ('yes i dislike cats because they don\'t love you', {'attitude': 'dislike', 'entity': 'cats', 'because': 'because', 'reason': 'they don\'t love you'})
    ]
    negative_examples = [
        'i love cats',
        'i\'m a big fan of dogs',
        'i don\'t really have an opinion',
        'i\'m not a big fan of dogs', # This will be caught by sentiment analysis
        'dogs are my least favorite animals' # This will be caught by sentiment analysis
    ]


def is_high_prec_yes(utterance : str) -> bool:
    return contains_phrase(utterance, set(YES))

def is_high_prec_no(utterance : str) -> bool:
    return contains_phrase(utterance, set(NO))

def is_high_prec_neutral(utterance : str) -> bool:
    return contains_phrase(utterance, set(NEUTRAL))

def is_high_prec_disinterest(utterance : str) -> bool:
    return utterance in EXIT

def is_high_prec_interest(utterance : str) -> bool:
    return utterance in CONTINUE

def is_like(utterance : str) -> Tuple[bool, Optional[str]]:
    """ High precision is_like check using regexes
    
    :param utterance: the utterance
    :type utterance: str
    :return: True if user said "i like ...", together with a reason if there is any
    :rtype: Tuple[bool, Optional[str]]
    """
    slots = LikeRegex().execute(utterance)
    if slots is None:
        return False, None
    return True, slots['reason'] if 'reason' in slots else None
    
def is_not_like(utterance : str) -> Tuple[bool, Optional[str]]:
    """ High precision is_not_like check using regexes
    
    :param utterance: the utterance
    :type utterance: str
    :return: True if user said "i don't like ...", together with a reason if there is any
    :rtype: Tuple[bool, Optional[str]]
    """
    slots = DislikeRegex().execute(utterance)
    if slots is None:
        return False, None
    return True, slots['reason'] if 'reason' in slots else None

def get_reasons(phrase : str) -> Tuple[List[str], List[str]]:
    """Returns a list of positive reasons and a list of negative reasons
    
    :param phrase: the phrase we are getting reasons for
    :type phrase: str
    :return: a list of positive reasons and a list of negative reasons
    :rtype: Tuple[List[str], List[str]]
    """
    opinions = opinion_sql.get_opinions(phrase.lower())
    positive_reasons = [opinion.reason for opinion in opinions if opinion.sentiment == 4]
    negative_reasons = [opinion.reason for opinion in opinions if opinion.sentiment == 0]
    return positive_reasons, negative_reasons
