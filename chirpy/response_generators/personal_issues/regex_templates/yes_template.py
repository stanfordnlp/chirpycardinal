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
    "yup",
    "ya",
    "uh-huh",
    "okay",
    "ok",
    "okey-dokey",
    "okey-doke",
    "yea",
    "aye",
    "course",
    "duh"
]

class YesTemplate(RegexTemplate):
    slots = {
        'yes_word': YES_WORDS,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{yes_word}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("yes let's keep talking", {'yes_word': 'yes'}),
        ("alright i will keep talking", {'yes_word': 'alright'})
    ]

    negative_examples = [
        "i don't want to talk about this any more",
        "can we talk about something else"
    ]


