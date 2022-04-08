from chirpy.core.util import contains_phrase
from chirpy.core.entity_linker.lists import STOPWORDS, get_unigram_freq
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.word_lists import INTENSIFIERS
from chirpy.core.regex.util import NONEMPTY_TEXT, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST, OPTIONAL_TEXT_MID, oneof, one_or_more_spacesep
from dataclasses import dataclass

OTHER_STOPWORDS = ['little', 'bit', 'feeling', 'pretty', 'feel',
                   'kind', 'kinda', 'guess', 'suppose', 'honestly',
                   'today', 'overall',
                   ] + INTENSIFIERS

GOOD_PHRASES = [
    'good', 'great', 'awesome', 'wonderful', 'excellent',
    'amazing', 'happy', 'well', 'positive', 'incredible', 'upbeat',

]

BAD_PHRASES = [
    'bad', 'sad', 'horrible', 'terrible', 'depressed', 'negative',
    'upset', 'crummy',
    'not ((too|very|so|that) )*{}'.format(oneof(GOOD_PHRASES)), 'down',
]

NEUTRAL_PHRASES = [
    'not ((too|very|so|that) )*{}'.format(oneof(BAD_PHRASES)), 'okay', 'ok', 'fine',
    'all right', 'alright', 'normal', "i don't know", 'better', 'find'
]


class GoodTemplate(RegexTemplate):
    slots = {
        'good': one_or_more_spacesep(GOOD_PHRASES),
        'preceder': OPTIONAL_TEXT_PRE,
        'follower': OPTIONAL_TEXT_POST,
    }
    templates = [
        "{preceder}{good}{follower}",
    ]
    positive_examples = [
        ('good thanks', {'preceder': '', 'good': 'good', 'follower': ' thanks'}),
        ('so great', {'preceder': 'so ', 'good': 'great', 'follower': ''}),
    ]
    negative_examples = [
        'okay',
    ]


class BadTemplate(RegexTemplate):
    slots = {
        'bad': one_or_more_spacesep(BAD_PHRASES),
        'preceder': OPTIONAL_TEXT_PRE,
        'follower': OPTIONAL_TEXT_POST,
    }
    templates = [
        "{preceder}{bad}{follower}",
    ]
    positive_examples = [
        ('bad to be honest', {'preceder': '', 'bad': 'bad', 'follower': ' to be honest'}),
        ('very bad', {'preceder': 'very ', 'bad': 'bad', 'follower': ''}),
        ('not so amazing i think', {'preceder': '', 'bad': 'not so amazing', 'follower': ' i think'}),
    ]
    negative_examples = [
    ]


class NeutralTemplate(RegexTemplate):
    slots = {
        'neutral': one_or_more_spacesep(NEUTRAL_PHRASES),
        'preceder': OPTIONAL_TEXT_PRE,
        'follower': OPTIONAL_TEXT_POST,
    }
    templates = [
        "{preceder}{neutral}{follower}",
    ]
    positive_examples = [
        ("i'm feeling okay today", {'preceder': "i'm feeling ", 'neutral': 'okay', 'follower': ' today'}),
        ("not so bad", {'preceder': "", 'neutral': 'not so bad', 'follower': ''}),
    ]
    negative_examples = [
    ]


good_template = GoodTemplate()
bad_template = BadTemplate()
neutral_template = NeutralTemplate()


def fits_template_no_elaboration(user_utterance, template) -> bool:
    """
    @param user_utterance: the user's utterance, responding to "how are you feeling?"
    @param template: A RegexTemplate (not the class, the initialized object)
    @return: True iff the user's utterance fits the template, and the "remaining" parts of the utterance (i.e. the
        'preceder' and 'follower' slots) contain only stopwords or other high frequency words.
    """

    # If it doesn't fit the template, return False
    slots = template.execute(user_utterance)
    if slots is None:
        return False

    # Get the preceder and follower parts
    preceder = slots.get('preceder', '').strip()
    follower = slots.get('follower', '').strip()

    # If "not" was in the preceder, return False
    if contains_phrase(preceder, {'not'}):
        return False

    # Go through words in the preceder and follower. If you find a "rare" word, return False
    other_words = preceder.split() + follower.split()
    for w in other_words:
        if w in STOPWORDS:
            continue
        if w in OTHER_STOPWORDS:
            continue
        if get_unigram_freq(w) > 2250:
            continue
        return False

    return True

@dataclass
class UserMood:
    GOOD_NO_ELAB = 'GOOD_NO_ELAB'
    BAD_NO_ELAB = 'BAD_NO_ELAB'
    NEUTRAL_NO_ELAB = 'NEUTRAL_NO_ELAB'
    OTHER = 'OTHER'


def classify_utterance_mood(user_utterance):
    """
    Analyzes the user's utterance, which is a response to "how are you feeling?".
    If the user is saying that they are good/bad/neutral without elaborating (i.e. without providing any other
    meaningful content), returns 'GOOD_NO_ELAB', 'BAD_NO_ELAB', 'NEUTRAL_NO_ELAB'. Otherwise, returns 'OTHER'.
    """
    if fits_template_no_elaboration(user_utterance, good_template):
        return UserMood.GOOD_NO_ELAB
    elif fits_template_no_elaboration(user_utterance, bad_template):
        return UserMood.BAD_NO_ELAB
    elif fits_template_no_elaboration(user_utterance, neutral_template):
        return UserMood.NEUTRAL_NO_ELAB
    else:
        return UserMood.OTHER