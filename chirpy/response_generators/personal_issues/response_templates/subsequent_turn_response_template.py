
from chirpy.annotators.corenlp import Sentiment
from chirpy.response_generators.personal_issues.response_templates.response_components import *
from chirpy.core.response_generator.response_template import ResponseTemplateFormatter

import logging

logger = logging.getLogger('chirpylogger')


class SubsequentTurnResponseTemplate(ResponseTemplateFormatter):
    slots = {
        "validate": FIRST_TURN_VALIDATE + STATEMENTS_VALIDATE,
        "question": QUESTIONS_REFLECTIVE + QUESTIONS_SOLUTION,
        "sharing": STATEMENTS_OFFER_LISTEN
    }

    templates = [
        "{validate} {question}",
        "{validate} {sharing}"
    ]


"""
For use in conjunction with GPT2's initial response
"""
class PartialSubsequentTurnResponseTemplate(ResponseTemplateFormatter):
    slots = {
        "question": QUESTIONS_REFLECTIVE + QUESTIONS_SOLUTION,
        "sharing": STATEMENTS_OFFER_LISTEN
    }

    templates = [
        "{question}",
        "{sharing}"
    ]


class ValidationResponseTemplate(ResponseTemplateFormatter):
    slots = {
        'acknowledgment': SUB_ACKNOWLEDGEMENT,
        'validate': STATEMENTS_VALIDATE
    }

    templates = [
        "{acknowledgment} {validate}"
    ]


class BackchannelResponseTemplate(ResponseTemplateFormatter):
    slots = {
        "backchannel": SUB_ACKNOWLEDGEMENT
    }

    templates = [
        "{backchannel}"
    ]
