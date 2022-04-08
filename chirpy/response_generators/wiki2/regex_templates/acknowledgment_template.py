from chirpy.response_generators.wiki2.response_templates.response_components import POSITIVE_ACKNOWLEDGEMENTS
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import *

class PositiveAcknowledgementTemplate(RegexTemplate):
    slots = {
        'acknowledgement': POSITIVE_ACKNOWLEDGEMENTS,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{acknowledgement}" + OPTIONAL_TEXT_POST,
        ]
    positive_examples = [
        ("that\'s cool", {'acknowledgement': 'cool'}),
    ]
    negative_examples = [
        'i don\'t understand',
    ]