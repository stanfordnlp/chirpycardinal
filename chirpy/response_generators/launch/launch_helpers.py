from enum import Enum, auto
import logging
import os
from typing import Optional
from chirpy.core.regex.templates import MyNameIsTemplate, DoesNotWantToSayNameTemplate
from chirpy.core.regex.word_lists import YES, NO
from typing import Optional, List, Tuple
from chirpy.core.util import load_text_file
from chirpy.core.response_generator.response_type import *
from chirpy.core.entity_linker.lists import get_unigram_freq
from chirpy.annotators.corenlp import Sentiment

logger = logging.getLogger('chirpylogger')


NAMES_FILEPATH = os.path.join(os.path.dirname(__file__), '../../core/regex/names.txt')
NAMES = load_text_file(NAMES_FILEPATH)
NAMES = [n.lower() for n in NAMES]
# logger.primary_info(f"Found {len(NAMES)} names.")

# Types of response that we might expect from the user
class UserIntent(Enum):
    no = auto()
    no_without_name = auto()
    no_with_name = auto()
    yes = auto()
    yes_without_name = auto()
    repeat = auto()
    why = auto()
    disinterested = auto()


ADDITIONAL_RESPONSE_TYPES = ['NEGATIVE_USER_SENTIMENT']
ResponseType = add_response_types(ResponseType, ADDITIONAL_RESPONSE_TYPES)


def could_be_name(utterance):
    if len(utterance.split()) == 1:
        # If utterance is not in our high-frequency spoken unigrams (except for mark), then it may be a name
        if get_unigram_freq(utterance) == 0 or utterance == 'mark':
            return True
    return False

def is_negative_user_sentiment(rg):
    """Determines if user had negative response. Returns bool"""
    return rg.state_manager.current_state.corenlp['sentiment'] == Sentiment.NEGATIVE or \
           rg.state_manager.current_state.corenlp['sentiment'] == Sentiment.STRONG_NEGATIVE

def get_name_from_utterance(rg, user_utterance, remove_no=False) -> Optional[str]:
    """

    :param user_utterance: user utterance
    :param remove_no: remove no words in the stripping step -- used by recognized_name_treelet
    :return:
    """
    # Next try matching with MyNameIs regex
    my_name_is_slots = MyNameIsTemplate().execute(user_utterance)

    proper_nouns = rg.state_manager.current_state.corenlp['proper_nouns']
    proper_nouns = list(proper_nouns) + list(word for word in rg.state_manager.current_state.text if word in NAMES and word not in proper_nouns)

    if my_name_is_slots:
        # Try to get proper nouns from name slot:
        name_slot = my_name_is_slots['name'].split()
        if "alexa" in proper_nouns:
            proper_nouns.remove("alexa")
        intersection = list(set(name_slot) & set(proper_nouns))
        if len(intersection) > 0:
            name = intersection[0]
            logger.primary_info(
                f'Detected MyNameIsIntent with name_slot={name_slot} and proper nouns in name_slot={intersection}. Choosing {name} as name.')
            return name

        # If no intersection, just use first word of name slot
        name = name_slot[0]
        logger.primary_info(
            f'Detected MyNameIsIntent with name_slot={name_slot}. Taking first word of name slot, {name}, as name.')
        return name

    # If no name slot, just try proper nouns
    if proper_nouns:
        name = proper_nouns[0]
        logger.primary_info(
            f'Didn\'t detect MyNameIsIntent. Have proper_nouns={proper_nouns}. Using first one, {name}, as name')
        return proper_nouns[0]

    # Otherwise, if the user only said one word, and it's not a high-frequency unigram, assume that's the name
    stripped_user_utterance = user_utterance.split()
    for yes_word in YES:
        if yes_word in stripped_user_utterance:
            stripped_user_utterance.remove(yes_word)
    if remove_no:
        for no_word in NO:
            if no_word in stripped_user_utterance:
                stripped_user_utterance.remove(no_word)
    stripped_user_utterance = " ".join(stripped_user_utterance)
    if could_be_name(stripped_user_utterance):
        logger.primary_info('Didn\'t detect MyNameIsIntent, but utterance is length 1 and is not a high-frequency unigram, so assuming name={}'.format(stripped_user_utterance))
        return stripped_user_utterance

    return None
