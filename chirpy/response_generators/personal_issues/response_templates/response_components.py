"""
    Trenton Chang, Caleb Chiam - Nov. 2020
    response_components.py

    The following file contains sub-response units that are used by ResponseTemplate classes to return modular utterances to
    Treelets.

    Table of Contents:
    1. BEGIN_LISTEN
    2. SUB_*: sub-sentence/response level units
    3. STATEMENTS_*: full sentences
    4. QUESTIONS_*: questions for the user
    5. WORD_*: single word units

    Please try to keep it in alphabetical order by section!

"""

##################################################################
#
#   SECTION 1: BEGIN_LISTEN
#
##################################################################

BEGIN_LISTEN = [
    "Thank you for sharing that with me."
]

##################################################################
#
#   SECTION 2: SUB_*
#
##################################################################

SUB_ACKNOWLEDGEMENT = [
    "Mhm, I see.",
    "Right, I see.",
    "Ah, okay then.",
    "I see.",
    "Mm, I see.",
    "Alright, I see.",
    "Mhm, I hear you."
]

SUB_EMOTION_INFINITIVE = [
    "to hear", "to see"
]


SUB_NEG_EMOTION_WORDS = [
    "annoyed", 
    "frustrated", 
    "sad", 
    "disappointed"
    ]

SUB_NEUTRAL_PRE_INTERJECTION = [
    "so"
]

SUB_SUBJUNCTIVE_PRE = [
    "i'm {bot_personal_emotion} {emotion_infinitive} that",
    "it's {objective_emotion} that",
    "it must be {objective_emotion} that",
    "i feel {bot_personal_emotion} {emotion_infinitive} that",
    "you must feel {user_personal_emotion} that",
    "it sounds like you're {user_personal_emotion} that",
    "{tentafier} you're {user_personal_emotion} that"
]

SUB_TAG_QUESTION = [
    "?",
    ", right?",
    ", is that right?",
]

SUB_TENTAFIERS = [
    "it sounds like ",
    "it seems like ",
    "it sounds like you're saying that ",
    "i feel like you're saying that "
]

SUB_YES = [
    "Okay.", 
    "Sure thing.",
    "That's fine.",
    "That's alright."
]



##################################################################
#
#   SECTION 3: STATEMENTS_*
#
##################################################################

STATEMENTS_OFFER_LISTEN = [
    "I'm here to listen if you would like to tell me more.",
    "I would be interested to hear more if you don't mind sharing.",
    "Feel free to continue telling me more.",
    "Please continue telling me more if you would like to.",
    "I'm willing to hear more if you'd like to tell me about it.",
    "I'd be willing to listen if you're willing to continue sharing.",
]

STATEMENTS_LISTEN_SHORT = [
    "Okay, I'm listening.",
    "Go ahead, I'm listening."
]

STATEMENTS_EXPRESS_CONFUSION = [
    "Sorry, I don't understand what you're telling me.",
    "Sorry, I'm a little confused by that.",
    "Sorry, I don't see what you mean.",
    "Sorry, I'm not quite sure what you mean by that."
]



STATEMENTS_EXPRESS_OPINION = [
    "I'm glad that we talked about this.",
    "I'm happy that we got to talk about this."
]


"""
    general template:
        # TODO
"""
STATEMENTS_REASSURANCE = [
    "I hope things will turn out alright.",
    "I hope you'll be fine.",
    "I hope you will be kind to yourself even when things are difficult.",
    "As with all things, we can only take it one step at a time.",
    "I hope that you'll be able to find a way to make the best of this situation, even if it's not what you wanted.",
    "I hope things will turn out alright in the end, no matter how difficult they may seem now.",
]


"""
    general template:
        [Accepting phrase] + [Change of subject prompt]
"""
STATEMENTS_REJECTION_HANDLING = [
    "That's okay. Thanks for ",
    "That's fine. I'm always here to listen if you need though."
]

STATEMENTS_THANKING = [
    "Thank you for talking to me about this today.",
    "Thanks for sharing this with me."
]

FIRST_TURN_VALIDATE = [
    "I'm sorry to hear that.",
    "That sounds difficult.",
    "That's really unfortunate."
]

STATEMENTS_VALIDATE = [
    "That sounds frustrating.",
    "How awful, I'm sorry.",
    "That's tough and really unfortunate.",
    # "I'm sorry to hear you're going through that.",
    # "You must be going through a really hard time.",
    # "I'm sorry you are going through this.",
]

##################################################################
#
#   SECTION 4: QUESTIONS_*
#
##################################################################

QUESTIONS_ANYTHING_ELSE = [
    "Would you like to tell me more about this?",
    "Is there anything else you would like to tell me about this?",
    "Was there something else you would like to talk about regarding this?",
    "Is there anything else you would like to bring up?"
]


QUESTIONS_CHANGE_SUBJECT = [
    "We can talk about something else if you'd like?",
    "Shall we talk about something else?",
    "Is there another topic you'd like to discuss?"
]

STATEMENTS_CHANGE_SUBJECT = [
    "Let's talk about something else then."
]

QUESTIONS_ENCOURAGE_SHARING = [
    # "Could you elaborate?" -- too aggro
    "Would you like to tell me more about that?",
    "Would you like to talk more about that?",
    "Do you want to talk about this more?",
    "Do you want to talk more about what happened?",
    "Would you like to tell me more about what happened?",
    "Are there any other things that happened that you would like me to know about?",
    "Is there anything else you want to tell me?",
    "Do you want to talk some more about this?"
]

QUESTIONS_REFLECTIVE = [
    "How long have you been feeling this way?",
    "Is there anything you've been doing to help cope with this?"
]

QUESTIONS_SOLUTION = [
    "Do you think the situation might improve soon?",
    "Is there anyone who might be able to help you get through this?"
]

##################################################################
#
#   SECTION 5: WORDS_*
#
##################################################################

"""
    Usage context: "I'm [WORD] that X"
"""
WORD_BOT_PERSONAL_EMOTION_NEGATIVE = [
    "sad", "sorry"
]

"""
    Usage context: "You seem [WORD] that X"
"""
WORD_USER_PERSONAL_EMOTION_NEGATIVE = [
    "frustrated", "angry", "displeased", "unhappy"
]

WORD_OBJECTIVE_EMOTION_NEGATIVE = [
    "frustrating", "annoying", "unfortunate", "sad", "difficult", "rough"
]



WORD_PERSONAL_EMOTION_POSITIVE = [
    "happy", "pleased", "glad", "content", "excited"
]

WORD_OBJECTIVE_EMOTION_POSITIVE = [
    "good", "nice", "great"
]

WORD_SUPERLATIVE = [
    "", "quite", "really"
]
