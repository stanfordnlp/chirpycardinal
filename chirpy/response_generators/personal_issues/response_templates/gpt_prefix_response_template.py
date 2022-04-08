from chirpy.response_generators.personal_issues.response_templates.response_components import *
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST
from chirpy.core.response_generator.response_template import ResponseTemplateFormatter

import logging

logger = logging.getLogger('chirpylogger')

PRIMER = [
    "hopefully",
    "I hope"
]

class GPTPrefixResponseTemplate(ResponseTemplateFormatter):
    slots = {
        "validate": STATEMENTS_VALIDATE,
        "primer": PRIMER
    }

    templates = [
        "{validate} {primer}"
    ]
