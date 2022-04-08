from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT, NONEMPTY_TEXT, \
    OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST, OPTIONAL_TEXT_MID


class ComplimentTemplate(RegexTemplate):
    slots = {
        "target": ["you", "you re", "your", "you're"],
        "compliment": ["amazing", "funny", "wonderful", "great", "cool", "nice", "awesome", "fantastic"],
        "pleasure": ["enjoy", "like", "enjoying", "liking"],
        "talk": ["talk", "talking", "conversation"],
        "i": ['i am', "i'm", "i"],
        "thank": ["thank you", "thanks"],
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{target}" + OPTIONAL_TEXT_MID + "{compliment}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{target}" + OPTIONAL_TEXT_MID + "{compliment}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "love you" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{i}" + OPTIONAL_TEXT_MID + "{pleasure}" + OPTIONAL_TEXT_MID +  "{talk}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{thank}" + OPTIONAL_TEXT_MID + "{talk}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{thank}" + OPTIONAL_TEXT_MID + "{target}" + OPTIONAL_TEXT_MID + "{talk}" + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ("you're the most amazing person ai ever", {"target": "you're", "compliment": "amazing"}),
        ("i love you alexa", {}),
        ("i like our conversation", {"i": "i", "pleasure": "like", "talk": "conversation"}),
        ("i like talking to you too", {"i": "i", "pleasure": "like", "talk": "talking"}),
        ("i enjoy my conversation with you", {"i": "i", "pleasure": "enjoy", "talk": "conversation"}),
        ("thank you for talking to me alexa", {"thank": "thank you", "talk": "talking"}),
        ("thanks for your conversation you made my day", {"thank": "thanks", "target": "your", "talk": "conversation"}),
    ]
    negative_examples = [
        "that wasn't funny"
    ]
