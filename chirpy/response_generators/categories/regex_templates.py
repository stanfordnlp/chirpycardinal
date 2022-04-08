from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import NONEMPTY_TEXT, OPTIONAL_TEXT_PRE_GREEDY, OPTIONAL_TEXT_POST
from chirpy.core.regex.word_lists import REQUEST_ACTION, CONTINUER


class CategoriesTemplate(RegexTemplate):
    # TODO-Kathleen: Can we avoid using continuer and just have "{keyword}" and "{request_action} {keyword}"?
    slots = {
        'continuer': CONTINUER,
        'request_action': REQUEST_ACTION,

        # TODO-Kathleen: Might be more natural to rename this slot to 'category'.
        #  Why not have this point to categories.keys(), your list of supported categories?
        #  Then this template would only match when the user is asking for a category. Currently it matches every nonempty string!
        'keyword': NONEMPTY_TEXT,
    }
    templates = [
        "{continuer} {request_action} {keyword}",
        "{request_action} {continuer} {keyword}",
        "{continuer} {keyword}",
        "{request_action} {keyword}",
        "{keyword}",
    ]
    # TODO-Kathleen: write tests
    positive_examples = []
    negative_examples = []

NEGATIVE_WORDS = ['boring', 'else', 'move on', 'ask', 'stupid', 'bad', 'dumb', 'don\'t watch']
class NegativeResponseTemplate(RegexTemplate):
    slots = {
        'negative_word': NEGATIVE_WORDS,
    }
    templates = [
        OPTIONAL_TEXT_PRE_GREEDY + "{negative_word}" + OPTIONAL_TEXT_POST,
        ]
    positive_examples = [
        ("that was boring", {'negative_word': 'boring'}),
        ("you are stupid", {'negative_word': 'stupid'}),
        ("that was in such a bad taste", {'negative_word': 'bad'}),
        ("i don't watch movies", {'negative_word': 'don\'t watch'}),
        ("i don't watch tv", {'negative_word': 'don\'t watch'}),
    ]
    negative_examples = [
        "that is so hamburger",
        "what do you mean",
        "i don't understand"
    ]
