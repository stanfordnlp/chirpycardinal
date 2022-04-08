from chirpy.core.regex.util import OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST, NONEMPTY_TEXT
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.templates import DontKnowTemplate

def process_til(til):
    return random.choice([
        f'I found out that {til}. Isn\'t that interesting?',
        f'I learned that {til}. What do you think about that?',
        f'Did you know that {til}?',
        f'I just found out the other day that {til}. Isn\'t that fascinating? What do you think?',
    ])

HANDOFF_REMARKS = [
    'Got it.',
    'Okay!',
    'OK',
    'I see!'
]

POSITIVE_ADJECTIVES = [
    "good",
    "pretty good",
    "the best",
    "best",
    "awesome",
    "amazing",
    "unbelievable",
    "superior",
    "high quality",
    "excellent",
    "superb",
    "outstanding",
    "magnificent",
    "exceptional",
    "marvelous",
    "wonderful",
    "first rate",
    "great",
    "ace",
    "terrific",
    "fantastic",
    "fabulous",
    "top notch",
    "killer",
    "wicked",
    "dope",
    "class",
    "awesome",
    "smashing",
    "brilliant",
    "extraordinary",
    "very much"
]
POSITIVE_VERBS = [
    "like",
    "love",
    "prefer",
    "adore",
    "enjoy",
    "did",
    "do",
    "liked",
    "loved",
    "prefered",
    "adored",
    "enjoyed"
]
POSITIVE_ADVERBS = [
    "really",
    "truly",
    "very",
    "honestly",
    "undoubtedly",
    "extremely",
    "thoroughly",
    "decidedly",
    "exceptionally",
    "exceedingly",
    "immensely",
    "monumentally",
    "tremendously",
    "incredibly",
    "most",
    "totally",
    "seriously",
    "real",
    "mighty",
    "just"
]
NEGATIVE_ADJECTIVES = [
    "bad",
    "pretty bad",
    "the worst",
    "worst",
    "poor",
    "second-rate",
    "unsatisfactory",
    "inadequate",
    "crummy",
    "appalling",
    "awful",
    "atrocious",
    "appalling",
    "deplorable",
    "terrible",
    "abysmal",
    "rotten",
    "godawful",
    "pathetic",
    "woeful",
    "lousy",
    "not up to snuff",
    "disagreeable",
    "terrible",
    "dreadful",
    "distressing",
    "horrific",
    "egregious"
]
NEGATIVE_VERBS = [
    "hate",
    "hated",
    "loathe",
    "loathed",
    "detest",
    "detested",
    "despise",
    "despised",
    "disliked",
    "abhored",
    "couldn't bear",
    "couldn't stand"
]

LIKE_CLAUSES = [
    'like',
    'like to',
    'love',
    'adore',
    'enjoy',
    'appreciate',
    'am a fond of',
    'am a fan of',
    'am a big fan of',
    'am a huge fan of',
    'am interested in',
    'i\'m a fond of',
    'i\'m  a fan of',
    'i\'m  a big fan of',
    'i\'m  a huge fan of',
    'i\'m  interested in'
]

DISLIKE_CLAUSES = [
    'dislike',
    'hate',
    'despise',
    'detest',
    'resent',
    'am turned off to',
    'i\'m turned off to',
    'do not appreciate',
    'don\'t like',
    'don\'t appreciate'
]

CHAT_CLAUSES = [
    "chat",
    "discuss",
    "converse",
    "talk",
    "tell",
    "chat with me",
    "converse with me",
    "talk to me",
    "tell me",
    "chat about",
    "converse about",
    "talk about",
    "chat with me about",
    "converse with me about",
    "talk to me about",
    "tell me about",
    "know anything about",
    "know something about",
    "i'm curious about",
    "i am curious about"
]

SURPRISE_EXPRESSIONS = [
    "wonderful!",
    "amazing!",
    "wow!",
    "oh great!",
    "nice!",
    "great!",
    "absolutely!",
    "alright!",
    "alrighty!",
]

DRY_EXPRESSIONS = [
    "i see.",
    "okay!",
    "ok!",
    "hmm,"
]

TO_BE = [
    'is',
    'are'
]

POSITIVE_ADVERBS = [
    "really",
    "truly",
    "very",
    "honestly",
    "undoubtedly",
    "extremely",
    "thoroughly",
    "decidedly",
    "exceptionally",
    "exceedingly",
    "immensely",
    "monumentally",
    "tremendously",
    "incredibly",
    "most",
    "totally",
    "seriously",
    "real",
    "mighty",
    "awful",
    "just"
]

POSITIVE_ADJECTIVES = [
    "good",
    "pretty good",
    "the best",
    "best",
    "awesome",
    "amazing",
    "unbelievable",
    "superior",
    "high quality",
    "excellent",
    "superb",
    "outstanding",
    "magnificent",
    "exceptional",
    "marvelous",
    "wonderful",
    "first rate",
    "great",
    "ace",
    "terrific",
    "fantastic",
    "fabulous",
    "top notch",
    "killer",
    "wicked",
    "dope",
    "class",
    "awesome",
    "smashing",
    "brilliant",
    "extraordinary"
]

RARE_WORDS = [
    'never',
    'rarely',
    'not',
    'dont',
    'do not',
    'don\'t'
]

NO = [
    "no",
    "absolutely not",
    "most certainly not",
    "of course not",
    "under no circumstances",
    "by no means",
    "not at all",
    "negative",
    "never",
    "not really",
    "nope",
    "uh-uh",
    "nah",
    "not on your life",
    "no way",
    "no way Jose",
    "ixnay",
    "nay"
]

YES = [
    "yes",
    "all right",
    "very well",
    "of course",
    "by all means",
    "sure",
    "certainly",
    "absolutely",
    "indeed",
    "right",
    "affirmative",
    "in the affirmative",
    "agreed",
    "roger",
    "aye aye",
    "yeah",
    "yep",
    "yup",
    "ya",
    "uh-huh",
    "okay",
    "ok",
    "okey-dokey",
    "okey-doke",
    "yea",
    "aye",
    "course"
]

MANY_RESPONSES = [
    "i honestly don't know, it is so hard to choose one, i guess i have too many.",
    "for me, trying to choose the one that i like the most is a hopeless act, i love them all.",
    "i have so much trouble choosing, i guess i don't have one specifically.",
    "i don't have a particular one."
]

POSITIVE_FEELINGS = [
    "happy",
    "excited",
    "wonderful",
    "lovely",
    "full of life",
    "bombastic",
    "careless",
    "relaxed",
    "alive",
    "great",
    "good"
]

NEGATIVE_FEELINGS = [
    "sad",
    "bored",
    "angry",
    "tired",
    "exhausted",
    "devastated",
    "horrified",
    "bad"
]

POSITIVE_WORDS = POSITIVE_ADJECTIVES + \
    POSITIVE_VERBS + \
    ['not ' + i for i in NEGATIVE_ADJECTIVES] + \
    ['not ' + i for i in NEGATIVE_VERBS] + \
    ['don\'t ' + i for i in NEGATIVE_ADJECTIVES] + \
    ['don\'t ' + i for i in NEGATIVE_VERBS] + \
    YES
NEGATIVE_WORDS = NEGATIVE_ADJECTIVES + \
    NEGATIVE_VERBS + \
    ['not ' + i for i in POSITIVE_ADJECTIVES] + \
    ['not ' + i for i in POSITIVE_VERBS] + \
    ['don\'t ' + i for i in POSITIVE_ADJECTIVES] + \
    ['don\'t ' + i for i in POSITIVE_VERBS] + \
    NO

ANSWER_FAVORITE_TEMPLATES = [
    OPTIONAL_TEXT_PRE + "my favorite {trigger_word} is (the |){answer}",
    OPTIONAL_TEXT_PRE + "my favorite is (the |){answer}",
    OPTIONAL_TEXT_PRE + "my favorite {trigger_word} of all time is (the |){answer}",
    OPTIONAL_TEXT_PRE + "my favorite of all time is (the |){answer}",
    OPTIONAL_TEXT_PRE + "my favorite {trigger_word} is probably (the |){answer}",
    OPTIONAL_TEXT_PRE + "my favorite is probably (the |){answer}",
    OPTIONAL_TEXT_PRE + "my favorite {trigger_word} of all time is probably (the |){answer}",
    OPTIONAL_TEXT_PRE + "my favorite of all time is probably (the |){answer}",
    OPTIONAL_TEXT_PRE + "i {like_word} (the |){answer}",
    OPTIONAL_TEXT_PRE + "i {positive_adverb} {like_word} (the |){answer}",
    OPTIONAL_TEXT_PRE + "i think (the |){answer} is {positive_adjective}",
    OPTIONAL_TEXT_PRE + "probably (the |){answer}",
    OPTIONAL_TEXT_PRE + "i'd have to say (the |){answer}",
    OPTIONAL_TEXT_PRE + "maybe (the |){answer}",
    OPTIONAL_TEXT_PRE + "i guess (the |){answer}",
    OPTIONAL_TEXT_PRE + "i think (the |){answer}",
    OPTIONAL_TEXT_PRE + "i listen to (the |){answer}",
    OPTIONAL_TEXT_PRE + "i like listening to (the |){answer}",
    OPTIONAL_TEXT_PRE + "it is (the |){answer}",
    OPTIONAL_TEXT_PRE + "it\'s (the |){answer}",
    "(the |){answer}"
]

class PositiveTemplate(RegexTemplate):
    slots = {
        'yes_word': YES
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{yes_word}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ('yeah', {'yes_word': 'yeah'}),
    ]
    negative_examples = [
        'no',
    ]

class NegativeTemplate(RegexTemplate):
    slots = {
        'no_word': NO + RARE_WORDS,
        'like_word': LIKE_CLAUSES,
        'dislike_word': DISLIKE_CLAUSES
    }
    templates = [
        OPTIONAL_TEXT_PRE + "(don\'t|do not) {like_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{no_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "(?<!don't ){dislike_word}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ('no', {'no_word': 'no'}),
        ('i don\'t like them', {'like_word': 'like'}),
    ]
    negative_examples = [
        'yeah',
    ]

DONT_KNOW_EXPRESSIONS = [
    'dont know',
    'don\'t know',
    'do not know',
    'not sure',
    'not so sure',
    'not quite sure',
    'no idea'
]

# class DontKnowTemplate(RegexTemplate):
#     slots = {
#         'dont_know': DONT_KNOW_EXPRESSIONS
#     }
#     templates = [
#         OPTIONAL_TEXT_PRE + "{dont_know}" + OPTIONAL_TEXT_POST
#     ]
#     positive_examples = [
#         ('i honestly don\'t know', {'dont_know': 'don\'t know'}),
#     ]
#     negative_examples = [
#         'i know',
#     ]

TOPIC_CHANGING_SIGNALS = [
    "Oh hey, on another topic,",
    "So, changing the subject a little,",
    "Anyway, um, on another subject,",
    "Hmm, so, on another topic,",
    "Oh hey, sorry to change the subject, but I just remembered that I wanted to ask you,",
    "Anyway, there’s actually something unrelated I wanted to ask you about,",
    "Oh hey, this is a bit random, but I just remembered something unrelated I wanted to ask you about,",
    "So, changing the gears a bit, I have been wondering,",
    "Okay, so, on another topic,",
    "So, changing the topic a bit, I wanted to ask you,",
    "Umm, so I hope you don't mind me changing the subject, but",
    "Hmm, I just thought of something I wanted to ask you. ",
    "So, umm, this is a little off topic, but",
    "Hey, if you don't mind me changing the topic, ",
    "If it's ok for me to change the subject, ",
    "This is unrelated to what we were talking about, but",
    "I hope you don't mind me going off topic, but",
    "Hey, so changing the topic, ",
    "This is kind of random, but ",
    "Hmm, there was actually something unrelated that I wanted to talk about. ",
    "Hey, I hope you don't mind me changing the subject. ",
    "Hmm I just remembered something else I wanted to talk about. "
]

QUESTION_CONNECTORS = [
    "I have been wondering,",
    "I wanted to ask you,",
    "I was thinking of asking you,",
    "Oh, on a related topic,",
    "Okay, so,",
    "Hmmm, let\'s see. Okay,",
    "Alright, then",
    "Okie dokie,"
]

SIMILAR_EXPRESSIONS = [
    "oh great!",
    "wonderful!",
    "amazing!",
    "wow!",
    "nice!",
    "great!",
    "absolutely!",
    "alright!",
]

TRIGGER_PHRASES = [
    'music',
    'songs',
    'musicians',
    'bands',
    'singers'
]

class ChatTemplate(RegexTemplate):
    slots = {
        'chat_clause': CHAT_CLAUSES,
        'trigger_word': TRIGGER_PHRASES
    }
    templates = [
        OPTIONAL_TEXT_PRE + "(?<!don't ){chat_clause} {trigger_word}" + OPTIONAL_TEXT_POST,
        "{trigger_word}"
    ]
    positive_examples = [
        ('let\'s chat about music', {'chat_clause': 'chat about', 'trigger_word': 'music'})
    ]
    negative_examples = [
        'i love music',
    ]
