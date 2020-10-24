"""
This file is a centralized place to collect common word lists to be used in regexes.
"""

YES = [
    "that's okay",
    "that's ok",
    "in the affirmative",
    "by all means",
    "all right",
    "very well",
    "of course",
    'go on',
    "yes",
    "ok",
    "sure",
    "yeah",
    "sure",
    "certainly",
    "absolutely",
    "indeed",
    "right",
    "affirmative",
    "agreed",
    "roger",
    "aye aye",
    "yeah",
    "yep",
    "yup",
    "ya",
    "uh-huh",
    "okay",
    "OK",
    "okey-dokey",
    "okey-doke",
    "yea",
    "aye",
    "course"
]

NO = [
    "no",
    'neither',
    'nothing',
    'nope',
    'none',
]

NEGATIVE_CONFIRMATION = [
    "no",
    "not",
    "nope"
]

POSITIVE_CONFIRMATION_CLOSING = [
    "yes",
    "yea",
    "yep",
    "ok",
    "sure",
    'yeah',
    'okay',
    "correct",
    "that's the case",
    "that is the case",
    "right",
    "stop",
    "end",
    "exit",
    "goodbye",
    "bye"
]

NEGATIVE_CONFIRMATION_CLOSING = [
    "keep talking",
    "keep going",
    "keep chatting",
    "continue",
    "don't stop",
    "do not stop",
    "don't exit",
    "do not exit",
    "don't end",
    "do not end",
    "don't go",
    "do not go",
    "don't mean",
    "do not mean",
    "didn't mean",
    "did not mean",
    "didn't want",
    "did not want",
    "don't want",
    "do not want",
    "not correct",
    "incorrect",
    "not right",
    "wrong",
    "not the case"
]

# These phrases mean the user is telling us their name, regardless of the context
MY_NAME_IS_NONCONTEXTUAL = [
    'my name is',
    "my name's",
    'my names',
    'my name',
    "i'm called",
    "i'm cold",
    'i am called',
    'call me',
]

# These phrases mean the user is telling us their name, regardless of the context
MY_NAME_IS_NOT = [
    'my name is not',
    'my name isn\'t',
    "my name's not",
    'my names not',
    'my name not',
    "i'm not called",
    "i'm not cold",
    'i am not called',
    'don\'t call me',
    'that\'s not my name',
    'that is not my name',
    'you got my name wrong',
    'what is my name',
    'do you know my name',
    'why don\'t you know my name',
    'why do you keep calling me that',
    'why do you keep calling me that name',
]


# These phrases mean the user is telling us their name, if we just asked them their name
MY_NAME_IS_CONTEXTUAL = [
    "i'm",
    'i am',
    "it's",
]

# This list contains stop words that may appear in other contexts.
# We only allow these words to be prepended by OPTIONAL_NAME_CALLING + OPTIONAL_STOP_PRE 
# and folllowed by OPTIONAL_STOP_POST.
STOP_AMBIGUOUS = [
    'off',
    'stop',
    'pause',
    'cancel',
    'exit'
]

OPTIONAL_NAME_CALLING = [
    '(let\'s (please )?)?'
    '(alexa (please )?)?',
    '(please (alexa )?)?'
]

OPTIONAL_STOP_PRE = [
    '(could you (please )?)?',
    '(can you (please )?)?',
    '(will you (please )?)?',
    '(would you (please )?)?',
]

OPTIONAL_STOP_POST = [
    '(( alexa)? please)?',
    '(( please)? alexa)?',
]

# For this list, we enable stop immediate if it is an prepended by OPTIONAL_NAME_CALLING + OPTIONAL_STOP_PRE
# and folllowed by OPTIONAL_STOP_POST.
# Otherwise, We route to CLOSING_CONFIRMATION RG if the utterance contains any of these phrases.
STOP = [
    "bye",
    "goodbye",
    "good bye",
    'stop talking',
    'stop the conversation',
    'stop chat',
    'stop chatting',
    'stop now',
    'shut down',
    'shut up',
    'go away',
    "i'm done",
    "i'm finished",
    "i'm leaving",
    "i have to go now",
    'good night',
    'turn off',
    'turn it off',
    'shut off',
    'power off',
    'end chat',
    'end conversation',
    'normal mode',
    'normal alexa',
    "can we stop",
    "can you stop",
    "stop computer",
    "goodbye",
    "be quiet",
    "leave me alone"
]

# We route to CLOSING_CONFIRMATION RG if the utterance contains any of these phrases.
STOP_LESS_PRECISE = [
    "i'm getting tired",
    "don't want to chat",
    'do not want to chat',
    'don\'t wan(na|t to) talk anymore',
    'don\'t wan(na|t to) chat anymore',
    'leave me alone',
    'stop (talking|asking)'
]

# Move the HIGH_THESHOLD for dialog act --> instead of stopping immediately to asking confirmation
# instead of having OPTIONAL_TEXT_PRE {empty/alexa}, OPTIONAL_TEXT_POST {empty/alexa} we have more precise phrase
# Everything we are currently catching --> move to closing confirmation (OPTIONAL_TEXT_PRE + "{stop}" + OPTIONAL_TEXT_POST)

# These phrases mean "how are you", regardless of when they're said by the user
HOWAREYOU_NONCONTEXTUAL = [
    'how are you',
    "how're you",
    "how's your day",
    'your day',
    "what's up with you",
    'what are you up to',
    'what are you doing',
]


# These phrases mean "how are you", if we just asked the user how their day is going
HOWAREYOU_CONTEXTUAL = [
    "how's yours",
    "how was yours",
    "how about yours",
    'how is yours',
    'and you',
    'how about you',
    "what about you",
]

WHATABOUTYOU = [
    'what about you',
    'how about you',
    "how's yours",
    "how was yours",
    "how about yours",
    'how is yours',
    "what's up with you",
    'and you',
    'what are you up to',
    'what are you doing'
]

CRITICISM = [
    'bad',
    'retarded',
    'stupid',
    'dumb',
    'buggy',
    'drunk',
    'annoying',
    'wrong',
    'idiot',
    'suck',
]

INTENSIFIERS = [
    'so',
    'very',
    'too',
    'really',
    'extremely',
    'quite',
    'pretty',
    'rather',
    'totally',
]

COMPLAINT_CLARIFY = [
    "say that again",
    "what do you mean",
    "what are you saying",
    "(who|what|why)( the hell| do| the fuck| nonsense)?( are| did)? (you|we) (talk|chat)(ing)? about",
    "what did you( just)? say",
    "(can|could|would|will) you( please)? repeat",
    "(can|could|would|will) you( please)? (say|ask|ask me|tell me) (that|this) (again|another time)",
    "repeat( that| this| what you( just)?( said| were saying)?)",
    "do( not|n't) (know|understand) what (you|that) (mean|means)",
    "(still |really )?do( not|n't)( really| even)? (know|understand) what you('re| are)? (saying|talking about|asking|telling)",
    "(no|any) idea what( the heck|the hell)? you('re| are) (saying|asking|telling|talking about)",
    "(which|what)(.*) are you talking about",
    "do( not|n't) (know|understand) what( the heck| the hell) (we|you)('re| are)? (talking about|asking|saying)",
    "do( not|n't) (know|understand) what( the heck| the hell)( are) (you|we) (talking about|asking|saying)",
    "i do( not|n't) follow",
    "but (i was(n't)?|you were(n't)?|we were(n't)?|you're( not)?|i'm( not)?|we're( not)?) talking about",
]

COMPLAINT_MISHEARD = [
    "i did(n't| not) (say|mean)",
    "not what i (said|meant)",
    "not what i('m| am) (saying|talking about)",
    "you did(n't| not) (hear|understand|listen)",
    "you('re| are) not (hear|understand|listen)(ing)?",
    "no i (said|meant)",
    "i never (said|meant)",
    "misheard( me| that)?",
    "heard (me|that|what i said) (wrong|incorrectly)",
    "do you (know|understand|remember) (what|who) (we are|we're|i am|i'm|we were) (talking about|saying)",
    "you do(n't| not)( even)? (know|understand|listen to) what i('m| am) (saying|talking about)",
    "(that|this)( is|'s) not (who|what|the 1|the one) i('m| am| was) (talking about|saying)",

]

COMPLAINT_REPETITION = [
    "you already (said|asked|told)",
    "you('re| are) repeating",
    "you (said|asked( me?)|told me) (that|this|the same)( thing| question)? (already|before|earlier)",
    "stop repeating",
    "you keep (saying|doing|asking|telling)",
    "you just (said|asked|told|did)",
    "(we|you) (just|already) talk(ed)? about( this| that)?"

]

COMPLAINT_PRIVACY = [
    "i do(n't| not) want to (tell|say)",
    "why (did|do) you ask",
    "why (did|do) you need to know",
    "(that's )?(not|none of) your business",
    "do(n't| not) ask me",
    "i('m| am) not going to (tell|say)( you| that)?",
    "i('m| am) not telling you"
]

NEGATIVE_WORDS = [
    "no",
    "don't",
    'neither',
    "i don't know",
    'else',
    'nothing',
    'nope',
    "haven't",
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
    "nay",
    "not",
    "nothing",
    "na",
    "nah",
    "but",
    "zero"
]