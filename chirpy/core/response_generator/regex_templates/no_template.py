from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT, OPTIONAL_TEXT_POST, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID
from chirpy.core.regex.word_lists import NEGATIVE_WORDS, CONTINUER

class NoTemplate(RegexTemplate):
    slots = {
        'neg_word': NEGATIVE_WORDS,
        'continuer': list(set(CONTINUER) - {'yes', 'yea', 'yeah'}),
        'safe': ["bad", "worries"]
    }
    templates = [
        "{continuer} {neg_word}(?! {safe})" + OPTIONAL_TEXT_POST,
        "{neg_word}(?! {safe})" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("no", {'neg_word': 'no'}),
        ("no i don't want to talk about that", {'neg_word': 'no'}),
        ("hmm nah i don't think so", {'continuer': 'hmm', 'neg_word': 'nah'}),
        ("not especially", {'neg_word': 'not especially'})
    ]
    negative_examples = [
        "ok",
        "sure",
        "ok please tell me more",
        "i would really like to hear more",
        "i have no food",
        "i have no idea",
        "not bad",
        "no worries",
        "hmm no worries",
        "okay, i've no idea what you said",
        "yes but i will talk to you later maybe tomorrow"
    ]