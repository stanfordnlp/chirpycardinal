from chirpy.core.response_generator.response_template import ResponseTemplateFormatter
from chirpy.response_generators.wiki2.response_templates.response_components import GENERAL_BOT_ACKNOWLEDGEMENTS

STATEMENTS_LISTEN_NEXT_TIME = [
    "I'm always here to listen if you need it.",
    "I'm always happy to listen if you'd like to talk about this again.",
    "I'll be here with a listening ear if you'd like to talk about this again."
    ""
]

QUESTION_USER_KNOWLEDGE = [
    "Do you know a lot about {}?",
    "Do you happen to know a lot about {}?",
    "Are you pretty familiar with {}?",
    "Are you especially knowledgeable about {}?",
    "{is_are} {} {some_one_thing} you know a lot about?",
    "Would you say that {} {is_are} {some_one_thing} you know a lot about?",
    "Do you know a great deal about {}?",
    "Would I be correct in guessing that you know a lot about {}?"
]


class CheckUserKnowledgeTemplate(ResponseTemplateFormatter):
    slots = {
        "ack": GENERAL_BOT_ACKNOWLEDGEMENTS,
        "qn": QUESTION_USER_KNOWLEDGE
    }

    templates = [
        "{qn}"
    ]
