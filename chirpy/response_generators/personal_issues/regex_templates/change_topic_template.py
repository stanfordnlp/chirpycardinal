from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT_POST, OPTIONAL_TEXT_PRE

CHANGE_TOPIC_PHRASE = [
    "talk about",
    "tell me about"
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
        ('can you tell me about wolves', {'change_topic': 'tell me about'})
    ]
    negative_examples = [
        "No, there isn't a problem",
    ]