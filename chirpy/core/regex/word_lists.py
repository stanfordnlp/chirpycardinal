"""
This file is a centralized place to collect common word lists to be used in regexes. Supports
regexes directly.
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
    "bye",
    "i am",
    "right",
    "that's right"
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
    'exit',
    'go home',
    'get out'
]

OPTIONAL_NAME_CALLING = [
    '(let\'s (please )?)?'
    '(alexa (please )?)?',
    '(please (alexa )?)?',
    '(thanks (alexa )?)?'
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
    "i have to go",
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
    "leave me alone",
    "unhook",
]

# We route to CLOSING_CONFIRMATION RG if the utterance contains any of these phrases.
STOP_LESS_PRECISE = [
    "i'm getting tired",
    "don't want to chat",
    'do not want to chat',
    'don\'t wan(na|t to) talk anymore',
    'don\'t wan(na|t to) chat anymore',
    'leave me alone',
    'stop (talking|asking)',
    "(can we |let's |can i )?talk( to you)? later",
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
    "what do you mean",
    "what are you saying",
    "(who|what|why)( the hell| do| the fuck| nonsense)?( are| did)? (you|we) (talk|chat)(ing)? about",
    "do( not|n't) (know|understand) what (you|that) (mean|means)",
    "(still |really )?do( not|n't)( really| even)? (know|understand) what you('re| are)? (saying|talking about|asking|telling)",
    "(no|any) idea what( the heck|the hell)? you('re| are) (saying|asking|telling|talking about)",
    "(which|what)(.*) are you talking about",
    "do( not|n't) (know|understand) what( the heck| the hell) (we|you)('re| are)? (talking about|asking|saying)",
    "do( not|n't) (know|understand) what( the heck| the hell)( are) (you|we) (talking about|asking|saying)",
    "i do( not|n't) follow",
    "but (i was(n't)?|you were(n't)?|we were(n't)?|you're( not)?|i'm( not)?|we're( not)?) talking about",
]

SAY_THAT_AGAIN = [
    "(say that|come|play that) again",
    "what did you( just)? say",
    "what did you( just)? play",
    "what was (that|the question)",
    "((can|could|would|will) you)?(( )?please)?( )?repeat( that| yourself)?( (again|(another|one more) time))?(( )?please)?",
    "((can|could|would|will) you)?(( )?please)?( )?(say|ask|ask me|tell me) (that|this) (again|(another|one more) time)(( )?please)?",
    "((can|could|would|will) you)?(( )?please)?( )?repeat( that| this| what you( just)?( said| were( just)? saying)?)(( )?please)?",
    "i (could|did)(n't| not)( quite)?( catch| hear| understand| get)( that| this| what you( just)?( said| were( just)? saying)?)",
    "what$",
    "say what$",
    "play what$",
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
    "i just (said|meant)",
]

COMPLAINT_REPETITION = [
    "you('re| are) repeating",
    "(i|you)( already| just)?( barely)?( said| asked( me?)| told( me| you )?)( that| this| the same)( thing| question)?( already| before| earlier| again)?(?! so)",
    "(i|you)( already| just)( barely)?( said| asked( me?)| told( me| you )?)( that| this| the same)?( thing| question)?( already| before| earlier| again)?(?! so)",
    "stop( repeating| saying)( this| that| the same)?( thing| question)?",
    "you keep (saying|doing|asking|telling)",
    "(we|you)( just| already) talk(ed)? about( this| that)?",
]

COMPLAINT_PRIVACY = [
    "i do(n't| not) want to (tell|say)",
    "why (did|do) you ask",
    "why (did|do) you need to know",
    "(that's )?(not|none of) your business",
    "do(n't| not) ask me",
    "i('m| am) not going to (tell|say)( you| that)?",
    "i('m| am) not telling you",
    "that's( a)?personal( question)?"
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
    "not especially",
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

CONTINUER = [
    "ah",
    "aah",
    "absolutely",
    "agreed",
    "aha",
    "ahem",
    "ahh",
    "alexa",
    "alright",
    "alrighty",
    "amen",
    "anyhoo",
    "anyhow",
    "argh",
    "awww",
    "ay",
    "bah",
    "bravo",
    "cheers",
    "eh",
    "eww",
    "gee",
    "geepers",
    "golly",
    "goodness",
    "gosh",
    "great",
    "ha",
    "ha-ha",
    "hello",
    "hey",
    "hi",
    "hmm",
    "huh",
    "hurray",
    "indeed",
    "jeez",
    "man",
    "mm",
    "nah",
    "no",
    "now",
    "oh",
    "ooh",
    "oops",
    "ouch",
    "ow",
    "phew",
    "phooey",
    "please",
    "pooh",
    "right-o",
    "shoot",
    "shucks",
    "so",
    "thanks",
    "uh",
    "um",
    "ugh",
    "uh-huh",
    "uh-oh",
    "waa",
    "wahoo",
    "well",
    "whoa",
    "whoopee",
    "whoops",
    "whoosh",
    "wow",
    "yay",
    "yea",
    "yeah",
    "yes",
    "yikes",
    "yippee",
    "yo",
    "yoo-hoo",
    "yowza",
    "yuck",
    "yummy"
]

REQUEST_ACTION = [
    "talk",
    "chat",
    "discuss",
    "tell",
    "show",
    "say",
    "request",
    "switch",
    "change",
    "tell me",
    "give me",
    "get me",
    "bring me",
    "provide me",
    "show me",
    "elaborate on",
    "expand on",
    "switch to",
    "change to",
    "can you tell me",
    "can you give me",
    "can you show me",
    "can you say",
    "can i have",
    "can i listen to",
    "can you provide",
    "could you tell me",
    "could you give me",
    "could you show me",
    "could you say",
    "would you tell me",
    "would you give me",
    "would you show me",
    "would you say",
    "do you know",
    "did you know",
    "how about",
    "how about we talk about",
    "how about we chat about",
    "how about we discuss",
    "let's talk about",
    "talk about",
    "let's chat about",
    "chat about",
    "let's discuss",
    "discuss"
    "can we talk about",
    "can we chat about",
    "can we discuss",
    "can i hear",
    "i want",
    "i want to talk about",
    "i want to chat about",
    "i want to discuss",
    "i want to hear",
    "i'd like to talk about",
    "i'd like to chat about",
    "i'd like to discuss",
    "i'd like to hear",
    "i would love to talk about",
    "i would love to chat about",
    "i would love to discuss",
    "i would love to hear",
    "i'm interested in",
    "i'm curious about"
]

SECOND_PERSON = [
    "you",
    "you'll",
    "you're",
    "you've",
    "your"
]

WHAT_ABOUT_YOU_EXPRESSIONS = [
    "(what|how) about (you|you.|you?)",
]


DONT_KNOW_EXPRESSIONS = [
    'don(\')?t (really |actually |quite )?(know|remember)',
    'can(\')?t (really |actually |quite )?(remember|decide|choose|pick|name|think)',
    'not (really |quite )?know',
    'not (really |so |quite )?sure',
    'no (idea|clue)',
    '(hard|tough|difficult) (for me )?to (decide|choose|pick|name|think)',
    'don(\')?t have (1|one)'
]



BACK_CHANNELING_EXPRESSION = [
    '(that\'s |that )?cool',
    'yeah',
    'okay',
    'yes',
    'nice',
    'right',
    'uhuh',
    'uh'
]



EVERYTHING_EXPRESSIONS = [
    "a lot of",
    "lots of",
    "many",
    "everything",
]



NOTHING_EXPRESSIONS = [
    "nothing",
    "none",
    "don(\')?t have one",
    "don(\')?t have 1",
    "don(\')?t have a (favorite|favourite)",
    "nobody",
    "i'm not"
]


CLARIFYING_EXPRESSIONS = [
    "(were you|you were)( just)?( saying| asking| telling)( me)?( something)?( about)?( that)?",
    "(?<!(why ))((did|do) you( just)?( say| mean))( to say)?( that)?",
    "(i thought |heard )(i heard )?(you said)( that)?( i thought)?",
    "(i thought )(i heard )?you( asked| said| told)( to)?( me)?( about| i thought)?",
    "(i thought )(i heard )?you were( asking| talking) about( i thought)?"
]

HOW_QUESTION_PHRASES = [
    "how (can|do) you( really)?( even)?( do( this| that)| listen( to)?| walk| run| watch| eat| drink| see)( this| that)?",
    "can you( really)?( even)?( do( this| that)| listen( to)?| walk| run| watch| eat| drink| see)( this| that)?",
    "how are you( really)?( even)?( doing( this| that)| listening( to)?| walking| running| watching| eating| drinking| seeing)( this| that)?",
    "(how )?you('re| are)? a (ro)?bot",
    "(how )?you('re| are)? not( real(ly)?)?( a)?( real(ly)?)?( human| person| people| living| alive)"
]

WH_PERSONAL_QUESTION_PHRASES = [
    "(where|what'?s?|which|when)( one)?( do| did)?( you| your)",
    "what is it like( for you)?( in the cloud|( to be| being) a bot)?( for you)?",
    "i want to( hear| see)( about)?( what| why)?( you| your| yours)",
    "can you( tell| talk to) me( about)?( what)?( you| your| yours)",
    "have you( ever)?( done| been)",
    "if you( were| could)( be| do| have)?( any(thing)?)?",
    "do you( like| prefer| love| want| wanna| think)"
]

OFF_TOPIC_EXPRESSIONS = [ #TODO: for future use
    "((i thought)?( you| we) were( talking| telling| saying)( me| about)?",
]

GET_FACT_CHECKED_EXPRESSIONS = [ #TODO: for future use
    "that doesn't( sound| seem)( right| correct| true| accurate)",
    "don't( know| think)( if| that)? that's( actually| factually)?( right| correct| true| accurate)",
    "think( you| you're)( might be| are)?( wrong| incorrect| lying| messing)",
]

INTERRUPTION_EXPRESSIONS = [
    "i have a( question| something)",
    "can i( ask| say)( you)?( a)?( question| something)",
    "i( want(ed)?| would like) to ask( you)?( a)?(question| something)",
]

INTERJECTIONS = [
    "(wait( a( minute| sec(ond)?)?)?|hold( on| up))"
]

ADDRESSEE_EXPRESSIONS = [
    "for you",
    "(my)?( dude|buddy|friend|man|bro|bruh|girl|guy|alexa|sweetheart|kid)"
]

NEVER_MIND_EXPRESSIONS = [
    "never mind",
    "i( just)?( forgot|( don't| do not) remember)",
    "i( just)?( forgot|( don't| do not) remember)( what i was( saying| thinking| asking| going to( say| ask)))",
    "i( just)?( forgot|( don't| do not) remember)( what i wanted to( say| ask))",
    "i( just)?( forgot|( don't| do not) remember)( where i was going)",
    "i( just)?( forgot|( don't| do not) remember)(( my| the) question)",
]

SPORTS = [
    "football",
    "tennis",
    "baseball",
    "soccer",
    "basketball",
    "ping pong",
    # "table tennis", # TODO fix regex for table tennis: captures only 'tennis'
    "karate",
    "rowing",
    "running",
    "swimming",
    "gymnastics",
    "cheerleading",
    "badminton",
    "golf"
]

CUTOFF = [
    "(can|could|would) (you|i)",
    "i like",
    "i like to",
    "uh",
    "i",
    "i want",
    "((can|could|would) you |(can|could) we |let's |i wanna |i want to )?talk about",
    "((can|could|would) you )?tell me about",
    "i'm interested in",
]
