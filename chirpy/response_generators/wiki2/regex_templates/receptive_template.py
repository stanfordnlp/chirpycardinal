from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import *

class AppreciativeTemplate(RegexTemplate):
    """
    For detecting whether the user is appreciative of what they heard
    """
    slots = {
        'appreciation': ['wow', 'cool', 'interesting', 'neat', 'that makes sense', 'impressive', "awesome", "excellent",
                         'amazing', 'super', 'i like that', 'nice']
    }

    templates = [
        OPTIONAL_TEXT_PRE + '{appreciation}' + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ("huh, that's really interesting", {'appreciation': 'interesting'}),
        ("oh that's cool", {'appreciation': 'cool'}),
    ]
    negative_examples = [
        "that's pretty boring"
    ]

class KnowMoreTemplate(RegexTemplate):
    """
    For detecting whether the user wants to know more
    """
    slots = {
        'encourage': ['go on', 'tell me more', 'what else', 'share more', 'talk more', 'elaborate', 'anything else',
                      'continue', 'oh really', 'is that so', 'oh yeah'],
    }

    templates = [
        OPTIONAL_TEXT_PRE + '{encourage}' + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("oh can you tell me more about that", {'encourage': 'tell me more'}),
    ]
    negative_examples = [
        "that's pretty boring"
    ]

class AgreementTemplate(RegexTemplate):
    """
    For detecting whether the user wants to know more
    """
    slots = {
        'agree_phrase': ['exactly', 'i concur', "that's true", "right", "totally", "i know right",
                  "makes sense", 'i agree', 'agreed', 'me too'],
        'agree_word': ['agree', 'concur']
    }

    templates = [
        OPTIONAL_TEXT_PRE + '{agree_phrase}' + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "i" + OPTIONAL_TEXT_MID + '{agree_word}' + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("that makes sense to me", {'agree_phrase': 'makes sense'}),
        ('yeah i would agree', {'agree_word': 'agree'})
    ]
    negative_examples = [
        "that's pretty boring"
    ]

class DisagreementTemplate(RegexTemplate):
    """
    For detecting whether the user wants to know more
    """
    slots = {
        'action': ['agree', 'say', 'concur'],
        'disagree': ['disagree'],
        'not_phrase': ["wouldn't", "not", "don't"]
    }

    templates = [
        OPTIONAL_TEXT_PRE + "i" + OPTIONAL_TEXT_MID + '{not_phrase}' + OPTIONAL_TEXT_MID + '{action}' + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "i" + OPTIONAL_TEXT_MID + '{disagree}' + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("yeah i wouldn't say that", {'not_phrase': "wouldn't", 'action': 'say'}),
        ("i wouldn't say that", {'not_phrase': "wouldn't", 'action': 'say'}),
        ("i don't think i agree", {"not_phrase": "don't", 'action': 'agree'})
    ]
    negative_examples = [
        "yeah i agree"
    ]
