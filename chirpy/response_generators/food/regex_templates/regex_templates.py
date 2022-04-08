from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.response_generators.food.regex_templates.word_lists import *
from chirpy.core.regex.util import OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID, OPTIONAL_TEXT_POST, \
    OPTIONAL_TEXT_PRE_GREEDY, NONEMPTY_TEXT
from chirpy.core.regex.word_lists import CONTINUER

NEGATIVE_WORDS = ['not', "doesn't", "isn't", "hasn't", "won't", "don't", "didn't", 'no']
CORRECTNESS_MARKER = ["correct", "right", "clear", "good", 'sense', 'smart', 'understand', 'sure', 'true']
INCORRECTNESS_MARKER = ["incorrect", "wrong", "unclear", 'nonsense', 'nonsensical', 'stupid', 'unsure', 'untrue']

class DoubtfulTemplate(RegexTemplate):
    slots = {
        'negative_word': NEGATIVE_WORDS,
        'correctness_marker': CORRECTNESS_MARKER,
        'incorrectness_marker': INCORRECTNESS_MARKER
    }
    templates = [
        OPTIONAL_TEXT_PRE_GREEDY + "{negative_word}" + OPTIONAL_TEXT_MID + "{correctness_marker}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE_GREEDY + "{incorrectness_marker}" + OPTIONAL_TEXT_POST,
        'no', 'what'
        ]
    positive_examples = [
        ("that doesn't sound right", {'negative_word': "doesn't", 'correctness_marker': 'right'}),
        ("that's wrong", {'incorrectness_marker': 'wrong'}),
        ("that's stupid", {'incorrectness_marker': 'stupid'}),
        ("i don't understand", {'negative_word': "don't", 'correctness_marker': 'understand'}),
        ('no makes sense', {'negative_word': 'no', 'correctness_marker': 'sense'}),
        ('i\'m not sure about it', {'negative_word': 'not', 'correctness_marker': 'sure'})
    ]
    negative_examples = [
        'what do you mean',
        ]


class FavoriteTypeTemplate(RegexTemplate):
    slots = {
        'yes_word': YES_WORDS,
        'no_word' : NO_WORDS,
        'watch_word': WATCH_WORDS,
        'type': TYPES,
        'continuer' : CONTINUER,
        'positive_adjective': POSITIVE_ADJECTIVES,
        'positive_verb': POSITIVE_VERBS,
        'positive_adverb': POSITIVE_ADVERBS,
        'food': list(FOODS.keys())
    }
    templates = [
        "my favorite {food} is {type}",
        "my favorite is {type}",
        "my favorite {food} of all time is {type}",
        "my favorite of all time is {type}",
        "my favorite {food} is probably {type}",
        "my favorite is probably {type}",
        "my favorite {food} of all time is probably {type}",
        "my favorite of all time is probably {type}",
        "i {positive_verb} {type}",
        "i {positive_adverb} {positive_verb} {type}",
        "i think {type} is {positive_adjective}",
        "i follow {type}",
        "{continuer} my favorite {food} is {type}",
        "{continuer} my favorite is {type}",
        "{continuer} i {positive_verb} {type}",
        "{continuer} i {positive_adverb} {positive_verb} {type}",
        "{continuer} i think {type} is {positive_adjective}",
        "probably {type}",
        "{continuer} probably {type}",
        "i'd have to say {type}",
        "i guess i'd have to say {type}",
        "maybe {type}",
        "i guess {type}",
        "i think {type}",
        "{continuer} i'd have to say {type}",
        "{continuer} i guess i'd have to say {type}",
        "{continuer} maybe {type}",
        "{continuer} i guess {type}",
        "{continuer} i think {type}",
        "{yes_word} i {watch_word} {type}",
        "{yes_word} i recently {watch_word} {type}",
        "{yes_word} lately i {watch_word} {type}",
        "{yes_word} i {watch_word} {type} recently",
        "{yes_word} i {watch_word} {type} lately",
        "{yes_word} i just {watch_word} {type}",
        "i {watch_word} {type}",
        "i recently {watch_word} {type}",
        "lately i {watch_word} {type}",
        "i {watch_word} {type} recently",
        "i {watch_word} {type} lately",
        "i just {watch_word} {type}",
        "i've seen {type}",
        "i've just seen {type}",
        "{continuer} {yes_word} i {watch_word} {type}",
        "{continuer} {yes_word} i recently {watch_word} {type}",
        "{continuer} {yes_word} lately i {watch_word} {type}",
        "{continuer} {yes_word} i {watch_word} {type} recently",
        "{continuer} {yes_word} i {watch_word} {type} lately",
        "{continuer} {yes_word} i just {watch_word} {type}",
        "{continuer} i {watch_word} {type}",
        "{continuer} i recently {watch_word} {type}",
        "{continuer} lately i {watch_word} {type}",
        "{continuer} i {watch_word} {type} recently",
        "{continuer} i {watch_word} {type} lately",
        "{continuer} i just {watch_word} {type}",
        "{yes_word} {type}",
        "{continuer} {type}",
        "{continuer} {yes_word} {type}",
        "{type}"
    ]

    positive_examples = []
    negative_examples = []
#
# class HaveYouHeardOfTemplate(RegexTemplate):
#     slots = {
#         'yes_word': YES_WORDS,
#         'no_word' : NO_WORDS,
#         'sport': NONEMPTY_TEXT,
#         'positive_adjective': POSITIVE_ADJECTIVES,
#         'positive_verb': POSITIVE_VERBS,
#         'positive_adverb': POSITIVE_ADVERBS,
#     }
#     templates = [
#         "{yes_word}",
#         "{no_words}",
#         "{yes_word} I have"
#         "{no_words} I have not"
#         "{no_words} I haven't"
#     ]
