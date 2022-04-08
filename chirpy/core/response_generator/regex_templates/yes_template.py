"""
Adapted from movies RG's YesTemplate
"""

from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT, OPTIONAL_TEXT_POST, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID

YES_WORDS = [
    "yes",
    "all right",
    "alright",
    "very well",
    "of course",
    "by all means",
    "sure",
    "certainly",
    "absolutely",
    "indeed",
    "right",
    "affirmative",
    "in the affirmative",
    "agreed",
    "roger",
    "aye aye",
    "yeah",
    "yep",
    "yeap",
    "yup",
    "ya",
    "uh-huh",
    "okay",
    "ok",
    "okey-dokey",
    "okey-doke",
    "yea",
    "aye",
    "duh",
    "guess so",
    "kind of",
]

SINGLE_YES_WORDS = [
    'course' # prevent false positives like "course of medication"
]

class YesTemplate(RegexTemplate):
    slots = {
        'yes_word': YES_WORDS,
        'single_word': SINGLE_YES_WORDS,
        'neutral_positive': ['guess'],
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{yes_word}" + OPTIONAL_TEXT_POST,
        "{single_word}",
        "i {neutral_positive}",

    ]
    positive_examples = [
        ("yes let's keep talking", {'yes_word': 'yes'}),
        ("alright i will keep talking", {'yes_word': 'alright'}),
        ("course", {'single_word': 'course'})
    ]

    negative_examples = [
        "i don't want to talk about this any more",
        "can we talk about something else",
        # "not right now"
    ]

class NotYesTemplate(RegexTemplate):
    """
    Catching false positives caused by YesTemplate
    """
    slots = {
        'phrase': ['right now']
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{phrase}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("i'm not watching any tv show right now", {'phrase': 'right now'})
    ]

    negative_examples = [
    ]
