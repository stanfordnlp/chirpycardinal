from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT_POST, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID

GRATITUDE_WORDS = ['helpful', 'appreciate', 'nice', 'thanks', 'thank', 'thank you', 'awesome', 'lovely', 'grateful']
NEGATING_WORDS = ["not", "doesn't", "isn't", "don't", "won't", "wouldn't", "can't", "shouldn't",
                  "couldn't", "wasn't", "didn't", "shan't", "ain't", "aren't", "no"]


class GratitudeTemplate(RegexTemplate):
    slots = {
        'gratitude_word': GRATITUDE_WORDS,
    }
    
    templates = [
        OPTIONAL_TEXT_PRE + "{gratitude_word}" + OPTIONAL_TEXT_POST
    ]

    positive_examples = [
        ("thank you very much", {'gratitude_word': 'thank'}),
        ("thanks for saying that", {'gratitude_word': 'thanks'}),
        ("i appreciate that", {'gratitude_word': 'appreciate'}),
        ("you're an awesome listener", {'gratitude_word': 'awesome'})
    ]

    negative_examples = [
        "i don't know",
        "where's the beef",
        # "i don't appreciate you saying that",
        # "no thanks"
    ]


class NegatedGratitudeTemplate(RegexTemplate):
    slots = {
        'gratitude_word': GRATITUDE_WORDS,
        'negator': NEGATING_WORDS
    }

    templates = [
        OPTIONAL_TEXT_PRE + "{negator}" + OPTIONAL_TEXT_MID + "{gratitude_word}" + OPTIONAL_TEXT_POST
    ]

    positive_examples = [
        ("no thanks", {'negator': 'no', 'gratitude_word': 'thanks'}),
        # ("i don't think that's nice", {'negator': "don't", ''},
        ("that's not helpful", {'negator': 'not', 'gratitude_word': 'helpful'})
    ]

    negative_examples = [
        "thank you, that was helpful"
    ]
