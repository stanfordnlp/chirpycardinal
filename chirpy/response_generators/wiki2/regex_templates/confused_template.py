from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import *

HIGH_PREC_QUESTION_WORD = [ "who", "who's", "where", "were", "where's", "what", "what's", "whats", "why", "why's", "when",
                            "when's", "which", "whose", "how"]
QUESTION_WORD = [ "who", "who's", "where", "were", "where's", "what", "what's", "whats", "why", "why's", "when",
                  "when's", "which", "whose", "how", "is", "did", "was", "can"]
CONVERSATIONAL_MARKER = ["say", "talking", "saying", "understand", "clarify", "mean", "said", "meant", "explain"]


class ClarificationQuestionTemplate(RegexTemplate):
    slots = {
        'q_word': QUESTION_WORD,
        'hq_word': HIGH_PREC_QUESTION_WORD,
        'conversational_marker': CONVERSATIONAL_MARKER,
    }
    templates = [
        OPTIONAL_TEXT_PRE_GREEDY + "{q_word}" + OPTIONAL_TEXT_MID + "{conversational_marker}" + OPTIONAL_TEXT_POST,
        "{q_word}",
        ]
    positive_examples = [
        ('what are you talking about', {'q_word': 'what', 'conversational_marker': 'talking'}),
        ('what do you mean', {'q_word': 'what', 'conversational_marker': 'mean'}),
        ('can you please clarify', {'q_word': 'can', 'conversational_marker': 'clarify'}),
        ('that is wrong what are you saying', {'q_word': 'what', 'conversational_marker': 'saying'}),
    ]
    negative_examples = [
        "i don't understand",
        "that doesn't make sense",
        "can we talk about games"
    ]

NEGATIVE_WORDS = ['not', "doesn't", "isn't", "hasn't", "won't", "don't", "didn't", 'no']
CORRECTNESS_MARKER = ["correct", "right", "clear", "good", 'sense', 'smart', 'understand', 'sure', 'true']
DOUBT_PHRASES = ["i don't think", "i doubt"]
INCORRECTNESS_MARKER = ["incorrect", "wrong", "unclear", 'nonsense', 'nonsensical', 'stupid', 'unsure', 'untrue']
class DoubtfulTemplate(RegexTemplate):
    slots = {
        'negative_word': NEGATIVE_WORDS,
        'correctness_marker': CORRECTNESS_MARKER,
        'incorrectness_marker': INCORRECTNESS_MARKER,
        'doubt_phrase': DOUBT_PHRASES
    }
    templates = [
        OPTIONAL_TEXT_PRE_GREEDY + "{negative_word}" + OPTIONAL_TEXT_MID + "{correctness_marker}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE_GREEDY + "{incorrectness_marker}" + OPTIONAL_TEXT_POST,
        'no', 'what',
        OPTIONAL_TEXT_PRE + "{doubt_phrase}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("that doesn't sound right", {'negative_word': "doesn't", 'correctness_marker': 'right'}),
        ("that's wrong", {'incorrectness_marker': 'wrong'}),
        ("that's stupid", {'incorrectness_marker': 'stupid'}),
        ("i don't understand", {'negative_word': "don't", 'correctness_marker': 'understand'}),
        ('no makes sense', {'negative_word': 'no', 'correctness_marker': 'sense'}),
        ('i\'m not sure about it', {'negative_word': 'not', 'correctness_marker': 'sure'}),
        ('i\'m not sure about that', {'negative_word': 'not', 'correctness_marker': 'sure'}),
        ("i don't think it's majestic", {'doubt_phrase': "i don't think"}),
        ("i doubt that's true", {'doubt_phrase': "i doubt"})
    ]
    negative_examples = [
        'what do you mean',
        'that would not be a good seat'
    ]