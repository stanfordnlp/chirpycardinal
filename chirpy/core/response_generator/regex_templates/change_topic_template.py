from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT_POST, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID

CHANGE_TOPIC_PHRASE = [
    "talk about",
    "tell me about"
]

SWITCH_PHRASE = [
    "switch",
    "change"
]

class ChangeTopicTemplate(RegexTemplate):
    slots = {
        'change_topic': CHANGE_TOPIC_PHRASE,
        'switch': SWITCH_PHRASE
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{change_topic}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{switch}" + OPTIONAL_TEXT_MID + "topic(s)?" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{switch}" + OPTIONAL_TEXT_MID + "talk" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{switch}" + OPTIONAL_TEXT_MID + "talking" + OPTIONAL_TEXT_POST
        ]
    positive_examples = [
        ("let's talk about grand theft auto", {'change_topic': 'talk about'}),
        ("i don't want to talk about it", {'change_topic': 'talk about'}),
        ('can we talk about food', {'change_topic': 'talk about'}),
        ('can you tell me about wolves', {'change_topic': 'tell me about'}),
        ("can we switch the topic", {'switch': "switch"}),
        ("can we switch to talking about wolves", {"switch": "switch"}),
        ("let's change topics", {"switch": "change"})
    ]
    negative_examples = [
        "No, there isn't a problem",
        "i love playing on my nintendo switch"
    ]