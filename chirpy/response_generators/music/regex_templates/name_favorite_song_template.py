from chirpy.core.regex.util import *
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.response_generators.music.expression_lists import *
from chirpy.response_generators.food.regex_templates.word_lists import *


class NameFavoriteSongTemplate(RegexTemplate):
    # TODO-Kathleen: can we use OPTIONAL_TEXT_PRE instead of continuer and yes_word?
    slots = {
        'keyword_song': ['song', 'album', 'tune', 'melody', 'singer', 'artist', 'musician', 'band'],
        'favorite': NONEMPTY_TEXT,
        'positive_adjective': POSITIVE_ADJECTIVES,
        'positive_verb': POSITIVE_VERBS,
        'positive_adverb': POSITIVE_ADVERBS,
        'listen_word': ['listening to', 'hearing', 'listened to', 'heard', 'have been listening to', 'have been hearing', 'played', 'have been playing'],
        'yes_word': YES_WORDS,
    }
    templates = [
        "i {positive_verb} {listen_word} {favorite}",
        "my favorite {keyword_song} is {favorite}",
        "my favorite is {favorite}",
        "my favorite {keyword_song} of all time is {favorite}",
        "my favorite of all time is {favorite}",
        "my favorite {keyword_song} is probably {favorite}",
        "my favorite is probably {favorite}",
        "my favorite {keyword_song} of all time is probably {favorite}",
        "my favorite of all time is probably {favorite}",
        "i {positive_verb} {favorite}",
        "i {positive_adverb} {positive_verb} {favorite}",
        "i think {favorite} is {positive_adjective}",
        OPTIONAL_TEXT_PRE + "my favorite {keyword_song} is {favorite}",
        OPTIONAL_TEXT_PRE + "my favorite is {favorite}",
        OPTIONAL_TEXT_PRE + "i {positive_verb} {favorite}",
        OPTIONAL_TEXT_PRE + "i {positive_adverb} {positive_verb} {favorite}",
        OPTIONAL_TEXT_PRE + "i think {favorite} is {positive_adjective}",
        "probably {favorite}",
        OPTIONAL_TEXT_PRE + "probably {favorite}",
        "i'd have to say {favorite}",
        "i guess i'd have to say {favorite}",
        "maybe {favorite}",
        "i guess {favorite}",
        "i think {favorite}",
        OPTIONAL_TEXT_PRE + "i'd have to say {favorite}",
        OPTIONAL_TEXT_PRE + "i guess i'd have to say {favorite}",
        OPTIONAL_TEXT_PRE + "maybe {favorite}",
        OPTIONAL_TEXT_PRE + "i guess {favorite}",
        OPTIONAL_TEXT_PRE + "i think {favorite}",
        "{yes_word} i {listen_word} {favorite}",
        "{yes_word} i recently {listen_word} {favorite}",
        "{yes_word} lately i {listen_word} {favorite}",
        "{yes_word} i {listen_word} {favorite} recently",
        "{yes_word} i {listen_word} {favorite} lately",
        "{yes_word} i just {listen_word} {favorite}",
        "i {listen_word} {favorite}",
        "i recently {listen_word} {favorite}",
        "lately i {listen_word} {favorite}",
        "i {listen_word} {favorite} recently",
        "i {listen_word} {favorite} lately",
        "i just {listen_word} {favorite}",
        "i've heard {favorite}",
        "i've just heard {favorite}",
        OPTIONAL_TEXT_PRE + "{yes_word} i {listen_word} {favorite}",
        OPTIONAL_TEXT_PRE + "{yes_word} i recently {listen_word} {favorite}",
        OPTIONAL_TEXT_PRE + "{yes_word} lately i {listen_word} {favorite}",
        OPTIONAL_TEXT_PRE + "{yes_word} i {listen_word} {favorite} recently",
        OPTIONAL_TEXT_PRE + "{yes_word} i {listen_word} {favorite} lately",
        OPTIONAL_TEXT_PRE + "{yes_word} i just {listen_word} {favorite}",
        OPTIONAL_TEXT_PRE + "i {listen_word} {favorite}",
        OPTIONAL_TEXT_PRE + "i recently {listen_word} {favorite}",
        OPTIONAL_TEXT_PRE + "lately i {listen_word} {favorite}",
        OPTIONAL_TEXT_PRE + "i {listen_word} {favorite} recently",
        OPTIONAL_TEXT_PRE + "i {listen_word} {favorite} lately",
        OPTIONAL_TEXT_PRE + "i just {listen_word} {favorite}",
        "{yes_word} {favorite}",
        OPTIONAL_TEXT_PRE + "{favorite}",
        OPTIONAL_TEXT_PRE + "{yes_word} {favorite}",
        "{favorite}"
    ]
    # TODO-Kathleen: write tests
    positive_examples = []
    negative_examples = []
