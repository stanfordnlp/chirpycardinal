from chirpy.response_generators.one_turn_hack.responses import one_turn_responses
from chirpy.core.regex.regex_template import RegexTemplate


class ChattyTemplate(RegexTemplate):
    slots = {
        'chatty_phrase': [str(key) for key in one_turn_responses.keys()],
    }
    templates = [
        "{chatty_phrase}",
        "alexa {chatty_phrase}",
    ]
    positive_examples = [("talk about you", {'chatty_phrase': "talk about you"}),
                         ("can i have a conversation", {'chatty_phrase': "can i have a conversation"})]
    negative_examples = ["let's talk about movies",
                         "news",
                         "politics"]
