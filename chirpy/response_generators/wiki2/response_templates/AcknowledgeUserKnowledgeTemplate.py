from chirpy.core.response_generator.response_template import ResponseTemplateFormatter
from chirpy.response_generators.wiki2.response_templates.response_components import POS_ONE_WORD_ACKNOWLEDGEMENTS

QUESTION_USER_INTEREST = [
    "When did you start having an interest in {}?",
    "What got you interested in {}?",
    "How did you get interested in {}?",
    "Why are you interested in {}?",
    "When did you start being interested in {}?",
    "What made you interested in {}?"
]


class AcknowledgeUserKnowledgeTemplate(ResponseTemplateFormatter):
    slots = {
        "ack": POS_ONE_WORD_ACKNOWLEDGEMENTS,
        "qn": QUESTION_USER_INTEREST
    }

    templates = [
        "{ack}, {qn}"
    ]