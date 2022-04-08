from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT, NONEMPTY_TEXT, \
    OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST, OPTIONAL_TEXT_MID


class RequestStoryTemplate(RegexTemplate):
    slots = {
        "request": ["tell", "know", "narrate", "say"],
        "story": ["story", "stories"]
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{request}" + OPTIONAL_TEXT_MID + "{story}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{request}" + OPTIONAL_TEXT_MID + "{story}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("can you tell me a story", {"request": "tell", "story": "story"}),
        ("do you know any stories", {"request": "know", "story": "stories"}),
        ("i like you to tell me a story", {"request": "tell", "story": "story"}),
        ("tell me a story", {'request': 'tell', 'story': 'story'})
    ]
    negative_examples = [
    ]
