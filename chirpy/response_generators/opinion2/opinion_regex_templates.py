from chirpy.core.regex.util import OPTIONAL_TEXT_POST, OPTIONAL_TEXT_PRE
from chirpy.core.regex.regex_template import RegexTemplate

class WhatsYourOpinion(RegexTemplate):
    slots = {
        'asking_phrase' : ['do you like', "what's your opinion"]
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{asking_phrase}" + OPTIONAL_TEXT_POST, # match any utterance ending with these words
    ]
    positive_examples = [
        ('do you like bts', {'asking_phrase': 'do you like'}),
        ("what's your opinion on bts", {'asking_phrase': "what's your opinion"})
    ]
    negative_examples = [
        'i want to talk about bts',
        'tell me more about youtube'
    ]
