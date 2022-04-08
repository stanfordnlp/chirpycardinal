from chirpy.core.response_generator.response_template import ResponseTemplateFormatter
from chirpy.response_generators.personal_issues.response_templates.response_components import SUB_ACKNOWLEDGEMENT, \
    QUESTIONS_ANYTHING_ELSE, QUESTIONS_ENCOURAGE_SHARING, \
    QUESTIONS_CHANGE_SUBJECT, STATEMENTS_EXPRESS_CONFUSION, STATEMENTS_OFFER_LISTEN, SUB_YES

class PossibleContinueResponseTemplate(ResponseTemplateFormatter):
    slots = {
        "acknowledge": SUB_ACKNOWLEDGEMENT,
        "continue_questions": QUESTIONS_ANYTHING_ELSE + QUESTIONS_ENCOURAGE_SHARING #+ QUESTIONS_CHANGE_SUBJECT,
    }

    templates = [
        "{acknowledge} {continue_questions}"
    ]


class ConfusedPossibleContinueResponseTemplate(ResponseTemplateFormatter):
    slots = {
        "confusion": STATEMENTS_EXPRESS_CONFUSION,
        "continue_questions": QUESTIONS_ANYTHING_ELSE + QUESTIONS_CHANGE_SUBJECT,
    }

    templates = [
        "{confusion} {continue_questions}"
    ]


class PossibleContinueAcceptedResponseTemplate(ResponseTemplateFormatter):
    slots = {
        "ok": SUB_YES,
        "here_to_listen": STATEMENTS_OFFER_LISTEN,
        # "anything_else": QUESTIONS_ANYTHING_ELSE  // avoid repeating from PossibleContinue
    }

    templates = [
        "{ok} {here_to_listen}",
        # "{ok} {anything_else}"
    ]