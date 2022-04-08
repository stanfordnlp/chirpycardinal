from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT, NONEMPTY_TEXT, \
    OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST, OPTIONAL_TEXT_MID


class RequestAgeTemplate(RegexTemplate):
    slots = {
        "request": ["tell", "what's", "say", "what", "know"],
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{request}" + OPTIONAL_TEXT_MID + "your age" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{request}" + OPTIONAL_TEXT_MID + "your birthday" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "how old" + OPTIONAL_TEXT_MID + "you are" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "how old" + OPTIONAL_TEXT_MID + "are you" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("well how old are you", {}),
        ("what's your age alexa", {"request": "what's"}),
        ("tell me your age", {"request": "tell"}),
        ("tell me how old you are", {}),
        ("what's your birthday", {"request": "what's"}),
        ("do you know how old you are", {})
    ]
    negative_examples = [
        "how old do you think the earth is"
    ]
