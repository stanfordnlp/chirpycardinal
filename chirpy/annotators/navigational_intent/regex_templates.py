from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import one_or_more_spacesep, oneof, NONEMPTY_TEXT, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST
from chirpy.core.regex.word_lists import INTENSIFIERS
from chirpy.response_generators.fallback.response_templates import FALLBACK_PROMPTS
from chirpy.response_generators.neural_chat.util import question_part


TALK = [
    'talk',
    'talking',
    'chit',
    'chitchat',
    'chitchatting',
    'chit-chat',
    'chit-chatting',
    'chat',
    'chatting',
    'converse',
    'conversing',
    'discuss',
    'discussing',
    'learn',
    'learning',
    'tell',
    'telling',
    'speak',   # people ACTUALLY say this — Ethan
    'to know'
]

THIS = [
    "this",
    "that",
    "it",
    'those',
    'any',
    'of',
]

SOMETHING_ELSE = [
    "((something|anything) )+(else|different)+",
    "((the|some) )*{}( (topic|subject|thing))*".format(one_or_more_spacesep(['other', 'next'])),
]

CONVERSANTS = [
    'i',
    'you',
    'alexa',
    'we',
    'us',
    'he',
    'she',
    'they',
    "i'm",
    "you're",
    "we're",
    "she's",
    "he's",
    "they're",
    "i'll",
    "you'll",
    "we'll",
    "she'll",
    "he'll",
    "they'll",
    "i'd",
    "you'd",
    "we'd",
    "she'd",
    "he'd",
    "they'd",
    'me',
]

POSNAV_ANCHORS = [
    "can",
    "let's",
    "please",
] + CONVERSANTS

TALK_PHRASE_PRECEDERS = list(set([
    'please',
    'alexa',
    'continue',
    'okay',
    'cool',
    'keep',
    'on',
    'well',
    'yes',
    'yeah',
    'start',
    'just',
    'have',
    'a',
    'more',
    "let's",
    'am',
    'are',
    'is',
    'will',
    'was',
    'were',
    'should',
    'could',
    'would',
    'want',
    'wanna',
    'need',
    'like',
    'love',
    'can',
    'to',
    'think',
    'do',
    'mostly',
    'here',
    'might',
    'go',
    'ahead',
    'gonna',
    'did',
    'oh',
    'actually',
    'trying',
] + INTENSIFIERS + CONVERSANTS + POSNAV_ANCHORS))

# A talk phrase must have one or more TALK words, can optionally be preceded by TALK_PHRASE_PRECEDERS,
# and optionally followed by things like "to me more about"
TALK_PHRASE = "({preceder} )*{talk}( (to|with) {listener})*( {listener})*( (more|a|bit|little))*".format(
    preceder=oneof(TALK_PHRASE_PRECEDERS),
    talk=one_or_more_spacesep(TALK),
    listener=oneof(CONVERSANTS))

INTERESTED_IN = "({intensifier} )*(interested in|into)".format(conversant=one_or_more_spacesep(CONVERSANTS),
                                                               intensifier=oneof(INTENSIFIERS))

POSITIVE_NAVIGATION = [

    # This posnav template needs a posnav anchor (like "let's", "i", "can"), then one or more talk_phrases.
    # Anything can precede except "why do"
    "(?<!why do ){anchor} {talk_phrase}".format(anchor=one_or_more_spacesep(POSNAV_ANCHORS),
                                                talk_phrase=one_or_more_spacesep([TALK_PHRASE])),

    # This posnav template doesn't need a posnav anchor, but the talk phrase needs to be at the beginning of the utterance
    # We optionally allow "no" at the beginning of the utterance. This is not in TALK_PHRASE_PRECEDERS because it might signal
    # NegNav intent. However, users frequently say "no" at the beginning of the utterance before giving a PosNav intent
    "^(no )*{talk_phrase}".format(talk_phrase=one_or_more_spacesep([TALK_PHRASE])),

    # This is for things like "i'm interested in" / "we're really interested in"
    "(?<!why are ){conversant} ({preceder} )*{interested_in}".format(conversant=one_or_more_spacesep(CONVERSANTS),
                                                                    preceder=oneof(TALK_PHRASE_PRECEDERS),
                                                                    interested_in=one_or_more_spacesep([INTERESTED_IN])),

    "(?<!how )do you know" + OPTIONAL_TEXT_POST,
    "you (ever )?heard of" + OPTIONAL_TEXT_POST,
    "what do you think" + OPTIONAL_TEXT_POST,
]

NEGNAV_ANCHORS = [
    'stop',
    "don't",
    'not',
    "can't",
    'never',
    "wasn't",
    "weren't",
    "quit",
    "i'm done",
    "tired of",
    "hate"
]

NEGATIVE_NAVIGATION = [
    # This negnav template needs a negnav anchor (like "don't" or "stop"), then one or more talk_phrases.
    # If the talker is mentioned before the anchor, include it in the match
    # Anything can precede except "why"
    "(?<!why )({talker} )*{anchor} {talk_phrase}".format(anchor=one_or_more_spacesep(NEGNAV_ANCHORS),
                                                         talk_phrase=one_or_more_spacesep([TALK_PHRASE]), talker=oneof(CONVERSANTS)),

    # This is for things like "i'm not interested in" / "we were never really interested in"
    "(?<!why are ){anchor} {interested_in}".format(anchor=one_or_more_spacesep(NEGNAV_ANCHORS),
                                                                    interested_in=one_or_more_spacesep([INTERESTED_IN])),
]

NAV_QUESTION = [
    "what ((would|do|is it|topic|subject|should) )*(you|we) {talk_phrase}".format(talk_phrase=one_or_more_spacesep([TALK_PHRASE])),
    "what ((are|is it|that|topic|subject) )*(you|you're) {interested_in}".format(interested_in=one_or_more_spacesep([INTERESTED_IN])),
] + [question_part(q.lower()) for q in FALLBACK_PROMPTS]

HATE_PHRASE = [
    "i hate",
    "i don't like",
]

class NegativeNavigationTemplate(RegexTemplate):
    """
    This template captures when the user is expressing a negative navigational intent like
    "i don't want to talk about X", "i don't want to talk about", "i don't want to talk", "change the subject".
    """
    slots = {
        'change_the_subject': "(?<!don't )(change|new) (the )?(subject|category|topic)",
        'why_would_i': "why would (i|you)",
        'skip': "(let\'s )?skip( this)?",
        'nav': one_or_more_spacesep(NEGATIVE_NAVIGATION),
        'nav_about': one_or_more_spacesep([f'{oneof(NEGATIVE_NAVIGATION)} about']),
        'topic': NONEMPTY_TEXT,
        'change': "((move|change|switch) to|(talk|chat|discuss) about|discuss)",
        'subject': "(something else|(another|some other) (thing|subject|category|topic))",
        'hate': HATE_PHRASE,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{change_the_subject}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{why_would_i}" + OPTIONAL_TEXT_POST,
        "{skip}",
        OPTIONAL_TEXT_PRE + "{nav_about}( {topic})?",
        OPTIONAL_TEXT_PRE + "{nav}( {topic})?",
        OPTIONAL_TEXT_PRE + "{change} {subject}",
        OPTIONAL_TEXT_PRE + "{hate} {topic}",
    ]
    positive_examples = [
        ('change the subject', {'change_the_subject': 'change the subject'}),
        ('change the topic', {'change_the_subject': 'change the topic'}),
        ('new subject', {'change_the_subject': 'new subject'}),
        ('can we change the category', {'change_the_subject': 'change the category'}),
        ('change subject', {'change_the_subject': 'change subject'}),
        ('alexa change the subject please', {'change_the_subject': 'change the subject'}),
        ('stop talking about', {'nav_about': 'stop talking about'}),
        ('stop talking about movies', {'nav_about': 'stop talking about', 'topic': 'movies'}),
        ('oh my god please stop talking about movies', {'nav_about': 'stop talking about', 'topic': 'movies'}),
        ("i don't think i wanna talk to you anymore", {'nav': "don't think i wanna talk to you", 'topic': 'anymore'}),
        ("stop talking", {'nav': "stop talking"}),
        ("i'm not interested in spiders", {'nav': "not interested in", 'topic': 'spiders'}),
        ("we were never really interested in spiders", {'nav': "never really interested in", 'topic': 'spiders'}),
        ("i'm tired of talking about movies", {'nav_about': 'tired of talking about', 'topic': 'movies'}),
        ("i hate talking about this", {'nav_about': 'hate talking about', 'topic': 'this'}),
        ("i hate basketball", {'hate': 'i hate', 'topic': 'basketball'}),
    ]
    negative_examples = [
        'talk about movies',
        "don't change the subject",
        "no don't change the subject",
        "why don't you want to talk about it",
        "i'm interested in spiders",
        "why are you interested in spiders",
        # "i hate it"
    ]


class PositiveNavigationTemplate(RegexTemplate):
    """
    This template captures when the user is expressing a positive navigational intent like
    "i want to talk about X", "i want to talk about", "i want to talk".
    """
    slots = {
        'nav': one_or_more_spacesep(POSITIVE_NAVIGATION),
        'nav_about': one_or_more_spacesep(['{} about'.format(oneof(POSITIVE_NAVIGATION))]),
        'topic': NONEMPTY_TEXT,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{nav_about}( {topic})?",
        OPTIONAL_TEXT_PRE + "{nav}( {topic})?",
    ]
    positive_examples = [
        ('alexa can you please talk something else', {'nav': 'can you please talk', 'topic': 'something else'}),
        ('tell me jokes', {'nav': 'tell me', 'topic': 'jokes'}),
        ('tell me a bit', {'nav': 'tell me a bit'}),
        ("talk about zebras", {'nav_about': "talk about", 'topic': 'zebras'}),
        ("talk to me", {'nav': "talk to me"}),
        ("let's talk about zebras", {'nav_about': "let's talk about", 'topic': 'zebras'}),
        ("no i wanna learn about microbiology", {'nav_about': "i wanna learn about",  'topic': 'microbiology'}),
        ("can we chat about", {'nav_about': "we chat about"}),
        ("sure let's talk about it", {'nav_about': "let's talk about", 'topic': 'it'}),
        ("can you talk about life", {'nav_about': "you talk about",  'topic': 'life'}),
        ("can you tell me about golden buddha", {'nav_about': 'you tell me about', 'topic': 'golden buddha'}),
        ("talk more about it please", {'nav_about': 'talk more about', 'topic': 'it please'}),
        ("tell me a story about mexico", {'nav': 'tell me a', 'topic': 'story about mexico'}),
        ("i need to talk about you", {'nav_about': 'i need to talk about', 'topic': 'you'}),
        ("talk to me", {'nav': "talk to me"}),
        ("i would like to talk to you about cern", {'nav_about': "i would like to talk to you about", 'topic': 'cern'}),
        ("talk to me about ash wednesday", {'nav_about': "talk to me about", 'topic': 'ash wednesday'}),
        ("no tell me about your childhood", {'nav_about': "no tell me about", 'topic': 'your childhood'}),
        ("i don't want to talk about zebras i want to talk about giraffes", {'nav_about': "i want to talk about", 'topic': 'giraffes'}),
        ("tell me about giraffes i don't want to talk about zebras", {'nav_about': "tell me about", 'topic': "giraffes i don't want to talk about zebras"}),
        ("i'm interested in spiders", {'nav': "i'm interested in", 'topic': 'spiders'}),
        ("i am interested in sports", {'nav': "i am interested in", 'topic': 'sports'}),
        ("actually i'm really into arachnids", {'nav': "i'm really into", 'topic': 'arachnids'}),
        ("hey what do you know about whales", {'nav_about': 'do you know about', 'topic': 'whales'}),
        ("do you know anything about whales", {'nav_about': 'do you know anything about', 'topic': 'whales'}),
        ("alexa do you know much i'm not sure if you do but yeah anything about whales", {'nav_about': "do you know much i'm not sure if you do but yeah anything about", 'topic': 'whales'}),
        ("do you know whales live a hundred years", {'nav': 'do you know', 'topic': 'whales live a hundred years'}),
        ("have you ever heard of ariel osbourne", {'nav': 'you ever heard of', 'topic': 'ariel osbourne'}),
        ("what do you think about veganism", {'nav_about': 'what do you think about', 'topic': 'veganism'}),
        ("let's switch topics what do you think is going to happen", {'nav': 'what do you think', 'topic': 'is going to happen'}),
        ("yes i want to know about snow because i like snow", {'nav_about': 'i want to know about', 'topic': 'snow because i like snow'})
    ]
    negative_examples = [
        "into politics",
        "why do you want to talk about zebras",
        "stop talk about zebras",
        "don't talk about zebras",
        "i'm not interested in spiders",
        "why are you interested in spiders",
        "do you think i'm cool",
        "i haven't heard of it",
        "do you think so",
        "i don't know about that",
        "i don't know"
    ]


class SomethingElseTemplate(RegexTemplate):
    """
    This template captures when the input text contains a "something else" phrase.
    """
    slots = {
        'something_else': one_or_more_spacesep(SOMETHING_ELSE),
    }
    templates = [
        OPTIONAL_TEXT_PRE + '{something_else}' + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ("something else", {'something_else': "something else"}),
        ("uh something else please", {'something_else': "something else"}),
        ("any other topic would be better", {'something_else': "other topic"}),
        ("the next subject if you have one", {'something_else': "next subject"}),
    ]
    negative_examples = [
        "zebras",
        "this topic",
        "something fun",
    ]


class NavigationQuestionTemplate(RegexTemplate):
    """
    This template captures when the text is asking something like "what do you want to talk about".
    It's designed to be used on both user and bot utterances.
    """
    slots = {
        'nav_question': NAV_QUESTION,
    }
    templates = [
        OPTIONAL_TEXT_PRE + '{nav_question}' + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ("what would you like to talk about", {'nav_question': 'what would you like to talk'}),
        ("what should we talk about", {'nav_question': 'what should we talk'}),
        ("what do you want to chat about", {'nav_question': "what do you want to chat"}),
        ("that's very interesting thank you for sharing your thoughts so what subject would you like to discuss", {'nav_question': "what subject would you like to discuss"}),
        ("so tell me what are you interested in", {'nav_question': "what are you interested in"}),
        ("can you tell me one more time what you want to talk about", {'nav_question': 'what you want to talk'}),
    ]
    negative_examples = [
        "let's talk",
        "talk about zebras",
        "what are you talking about",
        "why are you interested in that",
    ]
