from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT_POST, OPTIONAL_TEXT_PRE

# https://www.thefreedictionary.com/List-of-pronouns.htm
PRONOUN_WORDS = [
    "i", "i'd", "i've", "i'll", "i'm"
    "we", "we'd", "we're", "we've", "we'll", "us", "ours",
    "he", "he'd", "he'll", "he's", "him", "his",
    "she", "she'd", "she'll", "she's", "her", "hers",
    "they", "they'd", "they'll", "they've", "they're", "them", "theirs"
    "me", "my", "myself", "mine"
] # specifically, personal/object/possessive pronouns + contractions, but you/yours, etc excluded

class PersonalPronounRegexTemplate(RegexTemplate):
    slots = {
        'pronoun_word': PRONOUN_WORDS
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{pronoun_word}" + OPTIONAL_TEXT_POST,
        ]
    positive_examples = [
        ("the doctors aren't sure if she will walk again", {'pronoun_word': "she"}),
        ("he'd call us names since we were young.", {'pronoun_word': "us"}),
        ("she'll be unhappy if I disappoint her", {'pronoun_word': "her"}),
        ("all by myself", {'pronoun_word': "myself"}),
        ("why would they do this to me", {'pronoun_word': "they"})
    ]
    negative_examples = [
        "No, there isn't a problem",
        'Did you want to talk about something?',
    ]