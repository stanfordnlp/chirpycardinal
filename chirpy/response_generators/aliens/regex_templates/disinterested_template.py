from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT_POST, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID

class DisinterestedTemplate(RegexTemplate):
    slots = {}

    templates = [
        OPTIONAL_TEXT_PRE + "don't" + OPTIONAL_TEXT_MID + "care" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + 'not' + OPTIONAL_TEXT_MID + 'interested' + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + 'do not' + OPTIONAL_TEXT_MID + 'care' + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "don't like" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "don't wanna" + OPTIONAL_TEXT_POST

    ]

    positive_examples = [
        ("i don't really care", {}),
    ]

    negative_examples = [
    ]

CHANGE_TOPIC_PHRASE = [
    "talk about",
    "tell me about",
    "switch"
]


class ChangeTopicTemplate(RegexTemplate):
    slots = {
        'change_topic': CHANGE_TOPIC_PHRASE
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{change_topic}" + OPTIONAL_TEXT_POST,
        ]
    positive_examples = [
        ("let's talk about grand theft auto", {'change_topic': 'talk about'}),
        ("i don't want to talk about it", {'change_topic': 'talk about'}),
        ('can we talk about food', {'change_topic': 'talk about'}),
        ('can you tell me about wolves', {'change_topic': 'tell me about'}),
        ("can we switch the topic", {'change_topic': "switch"})
    ]
    negative_examples = [
        "No, there isn't a problem"
    ]