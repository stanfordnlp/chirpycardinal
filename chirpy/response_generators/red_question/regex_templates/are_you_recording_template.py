from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT_POST, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID

class AreYouRecordingTemplate(RegexTemplate):
    slots = {
        'RECORD': ['record', 'recorded', 'records', 'recording'],
        'modifier': ['have', 'will be', 'will', 'are', 'like', 'like to', 'want to']
    }

    templates = [
        OPTIONAL_TEXT_PRE + "you {RECORD}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "you {modifier} {RECORD}" + OPTIONAL_TEXT_POST
    ]

    positive_examples = [
        ("do you record conversations", {'RECORD': 'record'}),
        ("are you recording this", {'RECORD': 'recording'}),
        ("are you recording this without my consent", {'RECORD': 'recording'}),
        ("alexa are you recording this conversation", {'RECORD': 'recording'}),
        ("echo are you recording this conversation", {'RECORD': 'recording'}),
        ("alexa have you recorded our conversations", {'RECORD': 'recorded'}),
        ("i bet you have recorded our conversations", {"RECORD": "recorded", "modifier": "have"}),
        ("do you like recording conversations", {"modifier": "like", "RECORD": "recording"})

    ]

    negative_examples = [
        "the government might be recording this interaction",
        "i don't like people listening in on my conversations",
        "you know people like to record conversations"
    ]
