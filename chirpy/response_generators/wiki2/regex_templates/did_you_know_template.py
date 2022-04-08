from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import *

class DidYouKnowQuestionTemplate(RegexTemplate):
    slots = {
        'q_word': ['did', 'do', 'have'],
        'verb': ['know', 'learn', 'heard', 'like', 'try', 'tried', 'hear', 'love', 'loved'],
    }
    templates = [
        OPTIONAL_TEXT_PRE_GREEDY + "{q_word} you (ever )?{verb}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("oh yeah, yeah, I'll have to check those out. Have you heard about Google's geospatial data visualization company? It's called keyhole, and it's used in google Earth!".lower(),
         {'q_word': 'have', 'verb': 'heard'}),

        ("I love Hawaii and have been to Hawaii! Do you know about that island where they united by the great king Kamehameha?".lower(),
         {'q_word': 'do', 'verb': 'know'}),
        ("have you ever tried Blue, the banana?",
         {'q_word': 'have', 'verb': 'tried'})
    ]
    negative_examples = [
        "i guess he suffers from a form of the depression that has happened with people before"
        "I heard that Anton Salonen caused an international incident after his Finnish father, with the help of Finnish diplomats, kidnapped his son back after the boys Russian mother kidnapped the boy in the first place. I wonder if he's a Finnish citizen?",
    ]