from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT_POST, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID


class DisinterestedTemplate(RegexTemplate):
    slots = {}

    templates = [
        OPTIONAL_TEXT_PRE + "don't" + OPTIONAL_TEXT_MID + "care" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + 'not' + OPTIONAL_TEXT_MID + 'interested' + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + 'do not' + OPTIONAL_TEXT_MID + 'care' + OPTIONAL_TEXT_POST,
        # OPTIONAL_TEXT_PRE + "don't like" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "don't wanna" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "i hate (this|it)"
    ]

    positive_examples = [
        ("i don't really care", {}),
        ("yeah i hate it", {})
    ]

    negative_examples = [
    ]
