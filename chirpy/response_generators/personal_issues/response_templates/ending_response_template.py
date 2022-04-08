from chirpy.core.response_generator.response_template import ResponseTemplateFormatter
from chirpy.response_generators.personal_issues.response_templates.response_components import STATEMENTS_THANKING, \
    STATEMENTS_EXPRESS_OPINION, STATEMENTS_OFFER_LISTEN, STATEMENTS_CHANGE_SUBJECT, STATEMENTS_REASSURANCE

STATEMENTS_LISTEN_NEXT_TIME = [
    "I'm always here to listen if you need it.",
    "I'm always happy to listen if you'd like to talk about this again.",
    "I'll be here with a listening ear if you'd like to talk about this again."
    ""
]

class EndingResponseTemplate(ResponseTemplateFormatter):
    slots = {
        "statement_thanking": STATEMENTS_THANKING,
        "express_opinion": STATEMENTS_EXPRESS_OPINION,
        "reassurance": STATEMENTS_REASSURANCE,
        "offer": STATEMENTS_LISTEN_NEXT_TIME, # note: a bit awkward to have this after express_opinion
        #  example: Thanks for sharing this with me. I'm happy that we got to talk about this. I'm here to listen to you. Do you want to talk about something else?
        "change_subject": STATEMENTS_CHANGE_SUBJECT
    }

    templates = [
        "{statement_thanking} {express_opinion} and {reassurance} {change_subject}",
        "{statement_thanking} {express_opinion} {change_subject}",
        "{statement_thanking} {reassurance} and {offer} {change_subject}"
    ]