"""This file is deprecated - we want to delete the contents once these functions are no longer being used"""

import logging
from chirpy.core.util import contains_phrase, is_exactmatch

logger = logging.getLogger('chirpylogger')

# List of nounphrases that might appear in user utterances, but we don't want to look them up in wikipedia, news, showerthoughts etc
# Should all be lowercase with no punctuation
DONT_LOOKUP_NOUNPHRASES = set(['news', 'movies', 'movie', 'alexa', 'your name', 'the name', 'my name', 'name',
                               'something else', 'thanks', 'thank you', 'nothing', 'question', 'a question',
                               'the subject', 'subject', 'conversation', 'the conversation', 'a conversation', 'corona'])

def is_dontlookup_nounphrase(nounphrase: str):
    """
    Checks whether the nounphrase is an exact match with something in DONT_LOOKUP_NOUNPHRASES.
    The check is case-blind (nounphrase will be lowercased and DONT_LOOKUP_NOUNPHRASES is already lowercase).

    THIS FN IS DEPRECATED AND SHOULDN'T BE USED
    """
    return is_exactmatch(nounphrase, DONT_LOOKUP_NOUNPHRASES, 'nounphrase "{}" is in DONT_LOOKUP_NOUNPHRASES',
                         lowercase_text=True, lowercase_phrases=False)


def contains_dontlookup_nounphrase(text: str):
    """
    Checks whether the text contains anything in DONT_LOOKUP_NOUNPHRASES.
    The check is case-blind (text will be lowercased and have punctuation removed, and DONT_LOOKUP_NOUNPHRASES is
    already lowercase with punctuation removed).
    Note that text might still be reasonable to lookup, even if it contains a "don't lookup" nounphrase.

    THIS FN IS DEPRECATED AND SHOULDN'T BE USED
    """
    return contains_phrase(text, DONT_LOOKUP_NOUNPHRASES, 'text "{}" contains DONT_LOOKUP nounphrase "{}"',
                           lowercase_text=True, lowercase_phrases=False,
                           remove_punc_text=True, remove_punc_phrases=False)
