from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT, NONEMPTY_TEXT, \
    OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST, OPTIONAL_TEXT_MID
from chirpy.response_generators.sports.sports_helpers import SPORTS

class RequestPlayTemplate(RegexTemplate):
    slots = {
        "request": ["alexa", "can you", "could you", "can we", "could we", "please", "let's"],
    }
    templates = [
        "{request}" + OPTIONAL_TEXT_MID + "play" + NONEMPTY_TEXT,
        "play " + NONEMPTY_TEXT
    ]
    positive_examples = [
        ("play drivers license", {}),
        ("play some music", {}),
        ("alexa play baby", {"request": "alexa"}),
        ("can you play you belong with me", {"request": "can you"}),
        ("can we play mad libs", {"request": "can we"}),
        ("play bon jovi", {}),
        ("let's play a game", {"request": "let's"})
    ]
    negative_examples = [
        "i like to play basketball",
        "playing video games", # what's your favorite thing to do?
        'i like to play computer games'
    ]

class NotRequestPlayTemplate(RegexTemplate):
    slots = {
        'activity': SPORTS + ["video game", "games", "outside"]
    }
    templates = [
        "play" + OPTIONAL_TEXT_MID + "{activity}",
        "play with" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "play a lot" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("play basketball", {'activity': 'basketball'}),
        ('play video games', {'activity': 'games'}),
        ('play with my friends', {}),
        ("play a lot of xbox", {})
    ]
    negative_examples = [
    ]