from chirpy.core.regex.word_lists import SAY_THAT_AGAIN
from chirpy.core.regex.regex_template import RegexTemplate

class SayThatAgainTemplate(RegexTemplate):
    slots = {
        "say_that_again": SAY_THAT_AGAIN
    }
    templates = [
        "{say_that_again}",
        "alexa {say_that_again}",
    ]
    positive_examples = [
        ("what did you just say", {"say_that_again": "what did you just say"}),
        ("could you please repeat yourself", {"say_that_again": "could you please repeat"}),
        ("alexa can you ask me that again", {"say_that_again": "can you ask me that again"}),
        ("repeat what you just said", {"say_that_again": "repeat what you just said"}),
        ("say that again", {"say_that_again": "say that again"}),
        ("alexa say that again please", {"say_that_again": "say that again"}),
    ]
    negative_examples = []
