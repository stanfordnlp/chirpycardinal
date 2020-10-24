"""
This file is a centralized place to collect commonly-used regex templates.
RECOMMENDATION: use this super useful website to construct and understand regexes: https://regexr.com/
"""

import logging
from chirpy.core.regex import word_lists
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import NONEMPTY_TEXT, OPTIONAL_TEXT, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST, oneof, one_or_more_spacesep


logger = logging.getLogger('chirpylogger')

class DoesNotWantToSayNameTemplate(RegexTemplate):
    slots = {
        'negative_word': word_lists.NEGATIVE_WORDS,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{negative_word}" + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ("no that's creepy", {'negative_word': "no"}),
    ]
    negative_examples = [
        'mmy name is abi',
        'my name',
    ]

class MyNameIsTemplate(RegexTemplate):
    slots = {
        'my_name_is_noncontextual': word_lists.MY_NAME_IS_NONCONTEXTUAL,
        'my_name_is_contextual': word_lists.MY_NAME_IS_CONTEXTUAL,
        'name': NONEMPTY_TEXT,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{my_name_is_noncontextual} {name}",  # this can be used to detect the user telling us their name at any point in the conversation
        OPTIONAL_TEXT_PRE + "{my_name_is_contextual} {name}",  # this should only be used to detect the user's name if we just asked them their name
    ]
    positive_examples = [
        ('my name is abi', {'my_name_is_noncontextual': 'my name is', 'name': 'abi'}),
        ('yes my name is abi', {'my_name_is_noncontextual': 'my name is', 'name': 'abi'}),
        ("it's abi", {'my_name_is_contextual': "it's", 'name': 'abi'}),
    ]
    negative_examples = [
        'mmy name is abi',
        'my name',
    ]

class MyNameIsNonContextualTemplate(RegexTemplate):
    slots = {
        'my_name_is_noncontextual': word_lists.MY_NAME_IS_NONCONTEXTUAL,
        'name': NONEMPTY_TEXT,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{my_name_is_noncontextual} {name}",  # this can be used to detect the user telling us their name at any point in the conversation
    ]
    positive_examples = [
        ('my name is abi', {'my_name_is_noncontextual': 'my name is', 'name': 'abi'}),
        ('yes my name is abi', {'my_name_is_noncontextual': 'my name is', 'name': 'abi'}),
    ]
    negative_examples = [
        'mmy name is abi',
        'my name',
        'i\'m tired'
    ]

class MyNameIsNotTemplate(RegexTemplate):
    slots = {
        'my_name_is_not': word_lists.MY_NAME_IS_NOT,
        'name': NONEMPTY_TEXT,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{my_name_is_not} {name}",
        OPTIONAL_TEXT_PRE + "{my_name_is_not}",
    ]
    positive_examples = [
        ('my name is not abi', {'my_name_is_not': 'my name is not', 'name': 'abi'}),
        ('that\'s not my name', {'my_name_is_not': 'that\'s not my name'}),
    ]
    negative_examples = [
        'my name is abi',
        'my name',
        'i\'m tired'
    ]

class HowAreYouTemplate(RegexTemplate):
    slots = {
        'how_are_you_noncontextual': word_lists.HOWAREYOU_NONCONTEXTUAL,
        'how_are_you_contextual': word_lists.HOWAREYOU_CONTEXTUAL,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{how_are_you_noncontextual}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{how_are_you_contextual}" + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ('how are you', {'how_are_you_noncontextual': 'how are you'}),
        ('it was good and you', {'how_are_you_contextual': 'and you'}),
        ('tell me about your day alexa', {'how_are_you_noncontextual': 'your day'}),
        ("great thanks how's yours", {'how_are_you_contextual': "how's yours"}),
    ]
    negative_examples = [
        "my day was good and i'm talking to you",
    ]

class WhatAboutYouTemplate(RegexTemplate):
    slots = {
        'what_about_you': word_lists.WHATABOUTYOU,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{what_about_you}" + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ('what about you', {'what_about_you': 'what about you'}),
        ('i\'m grateful for food what about you', {'what_about_you': 'what about you'}),
        ('it\'s hard to think of one but how about you', {'what_about_you': 'how about you'}),
    ]
    negative_examples = [
        "how are you",
    ]

class StopTemplate(RegexTemplate):
    slots = {
        'stop': word_lists.STOP_AMBIGUOUS + word_lists.STOP,
        'optional_name_calling': word_lists.OPTIONAL_NAME_CALLING,
        'optional_stop_pre': word_lists.OPTIONAL_STOP_PRE,
        'optional_stop_post': word_lists.OPTIONAL_STOP_POST
    }
    templates = [
        "{optional_name_calling}" + "{optional_stop_pre}" + "{stop}" + "{optional_stop_post}"
    ]
    positive_examples = [
        ('stop', {'optional_name_calling': '', 'optional_stop_pre': '', 'stop': 'stop', 'optional_stop_post': ''}),
        ('pause', {'optional_name_calling': '', 'optional_stop_pre': '', 'stop': 'pause', 'optional_stop_post': ''}),
        ('stop talking', {'optional_name_calling': '', 'optional_stop_pre': '', 'stop': 'stop talking', 'optional_stop_post': ''}),
        ('please stop', {'optional_name_calling': 'please ', 'optional_stop_pre': '', 'stop': 'stop', 'optional_stop_post': ''}),
        ('alexa stop', {'optional_name_calling': 'alexa ', 'optional_stop_pre': '', 'stop': 'stop', 'optional_stop_post': ''}),
        ('off', {'optional_name_calling': '', 'optional_stop_pre': '', 'stop': 'off', 'optional_stop_post': ''}),
        ('turn off', {'optional_name_calling': '', 'optional_stop_pre': '', 'stop': 'turn off', 'optional_stop_post': ''}),
        ('turn it off', {'optional_name_calling': '', 'optional_stop_pre': '', 'stop': 'turn it off', 'optional_stop_post': ''}),
        ('shut off', {'optional_name_calling': '', 'optional_stop_pre': '', 'stop': 'shut off', 'optional_stop_post': ''}),
        ('power off', {'optional_name_calling': '', 'optional_stop_pre': '', 'stop': 'power off', 'optional_stop_post': ''}),
        ('good night alexa', {'optional_name_calling': '', 'optional_stop_pre': '', 'stop': 'good night', 'optional_stop_post': ' alexa'}),
        ('please turn it off', {'optional_name_calling': 'please ', 'optional_stop_pre': '', 'stop': 'turn it off', 'optional_stop_post': ''}),
        ('would you stop', {'optional_name_calling': '', 'optional_stop_pre': 'would you ', 'stop': 'stop', 'optional_stop_post': ''}),
        ('shut off alexa', {'optional_name_calling': '', 'optional_stop_pre': '', 'stop': 'shut off', 'optional_stop_post': ' alexa'}),
        ('let\'s stop talking', {'optional_name_calling': 'let\'s ', 'optional_stop_pre': '', 'stop': 'stop talking', 'optional_stop_post': ''})
    ]
    negative_examples = [
        'i want to chat',
        'i hate stopping at red lights',
        'stopping',
        "i'm done with school",
        'i love jumping off planes',
        'why did pluto stop being a planet',
        'can we stop asking these questions',
        'no i don\'t stop',
        'you could tell cancel',
        'stop that please can you stop',
        'can you please stop i\'m not in youtuber i\'m just trying to see if i can call youtuber',
        'talking about space family drama but i\'m done',
        'because i love the puppy shut up and the movies',
        'would you stop asking me questions',
        'i was joking oh my god tickets casino know what i\'m done',
        'turn off my dad',
        'why did you stop',
        'no can we stop talking about movies i wanna talk about lizards',
        'no shut up i\'m talking about hymns',
        'okay i\'m done answering your questions alexa',
        'it\'s perfectly fine stop a green with everything i say'
    ]

class TryingToStopTemplate(RegexTemplate):
    """Match user trying to end the conversation"""
    slots = {
        "stop": ["end", "stop", "stopping", "don't like", "cancel", "exit", "off"],
        "conversation": ["conversation", "dialogue", "dialog", "chat", "chatting", "social mode", "social bot"],
        "stop_precise": word_lists.STOP + word_lists.STOP_LESS_PRECISE
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{stop}" + OPTIONAL_TEXT + "{conversation}" + OPTIONAL_TEXT_POST,
        "do you just talk all time",
        "help",
        OPTIONAL_TEXT_PRE + "{stop_precise}" + OPTIONAL_TEXT_POST
    ]

    positive_examples = [
        ("no why can't we can stop the chat", {"stop": "stop", "conversation": "chat"}),
        ("ending our conversation", {"stop": "end", "conversation": "conversation"}),
        ("do you just talk all time", {}),
        ("i don't like the chatting", {"stop": "don't like", "conversation": "chatting"}),
        ("that's enough i'm finished", {'stop_precise': "i'm finished"}),
        ('stop talking to me', {'stop_precise': 'stop talking'}),
        ('please leave me alone', {'stop_precise': 'leave me alone'}),
        ('i don\'t wanna talk anymore', {'stop_precise': 'don\'t wanna talk anymore'}),
        ('stop that please can you stop', {'stop_precise': 'can you stop'}),
        ('i don\'t have favorites now shut up', {'stop_precise': 'shut up'}),
        ('you can stop now', {'stop_precise': 'stop now'}),
        ('well i have to go now so bye stop', {'stop_precise': 'i have to go now'}),
        ('talking about space family drama but i\'m done', {'stop_precise': 'i\'m done'}),
        ('nice talking to you you have a good night', {'stop_precise': 'good night'}),
        ('i would like to stop chatting', {'stop': 'stop', 'conversation': 'chatting'}),
        ('okay i\'m done answering your questions alexa', {'stop_precise': 'i\'m done'}),
        ('i don\'t want to talk anymore', {'stop_precise': 'don\'t want to talk anymore'}),
        ("stop asking me questions", {"stop_precise": "stop asking"}),
        ("stop asking questions", {"stop_precise": "stop asking"})
    ]

    negative_examples = [
        "let's keep the conversation going",
        "i love this conversation",
        "i like talking about this conversation i have with my friend",
        "why did you stop"
    ]


class CriticismTemplate(RegexTemplate):
    slots = {
        'criticism': f"(({oneof(word_lists.INTENSIFIERS)}) )*({oneof(word_lists.CRITICISM)})+"
    }
    templates = [
        #  We could include "that's {criticism}", but that might catch instances where the user is criticising
        #  something we're discussing, rather than criticising the bot.
        OPTIONAL_TEXT_PRE + "you're {criticism}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "you are {criticism}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "you {criticism}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{criticism} alexa" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "alexa's {criticism}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "alexa is {criticism}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "what's wrong with you" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "i hate you" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("you're stupid", {'criticism': 'stupid'}),
        ("you're so stupid", {'criticism': 'so stupid'}),
        ("you're really really dumb", {'criticism': 'really really dumb'}),
        ("you're so buggy alexa", {'criticism': 'so buggy'}),
        ("why are you so bad", {'criticism': 'so bad'}),
        ("no stupid alexa", {'criticism': 'stupid'}),
        ("go home alexa you're drunk", {'criticism': 'drunk'}),
        ("that's dumb alexa", {'criticism': 'dumb'}),
        ("you suck alexa", {'criticism': 'suck'}),
        ("shut up alexa you're annoying", {'criticism': 'annoying'}),
        ("alexa is drunk", {'criticism': 'drunk'}),
        ("what's wrong with you", {}),
    ]
    negative_examples = [
        "you're so cool",
        "that's dumb",
        "do you think i'm stupid"
    ]

class ClosingNegativeConfirmationTemplate(RegexTemplate):
    """Match user confirmation that they are ending the conversation"""
    slots = {
        "no": word_lists.NEGATIVE_CONFIRMATION,
        "no_stop": word_lists.NEGATIVE_CONFIRMATION_CLOSING
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{no}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{no_stop}" + OPTIONAL_TEXT_POST,
        "i never meant that",
        "i still want to talk to you",
        "that's not what I said",
        "what are you talking about"
    ]
    # TODO: test this template
    positive_examples = [
        ("no", {"no": "no"}),
        ("no i still want to talk to you", {"no": "no"}),
        ("i never meant that", {}),
        ("wait no", {"no": "no"}),
        ("of course not", {"no": "not"}),
        ("nope", {"no": "nope"}),
        ("not really", {"no": "not"}),
        ("no i don't want to exit", {"no": "no"}),
        ("i don't want to exit", {"no_stop": "don't want"}),
        ("no don't stop", {"no": "no"}),
        ("no that's not what I said", {"no": "not"}),
        ("what are you talking about", {}),
        ("keep talking", {"no_stop": "keep talking"}),
        ("keep going", {"no_stop": "keep going"}),
        ("that's incorrect", {"no_stop": "incorrect"}),
        ("that's wrong", {"no_stop": "wrong"})
    ]

    negative_examples = [
        "ya",
        "yeah",
        "yes",
        "you can go",
        "bye",
        "yes exit",
        "goodbye"
    ]

class ClosingPositiveConfirmationTemplate(RegexTemplate):
    """Match user statement that they are not ending the conversation"""
    slots = {
        "pos_confirm": word_lists.POSITIVE_CONFIRMATION_CLOSING
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{pos_confirm}" + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ("yes", {"pos_confirm": "yes"}),
        ("yea", {"pos_confirm": "yea"}),
        ("yep", {"pos_confirm": "yep"}),
        ("stop talking", {"pos_confirm": "stop"}),
        ("stop", {"pos_confirm": "stop"}),
        ("goodbye", {"pos_confirm":"goodbye"}),
        ("bye", {"pos_confirm": "bye"}),
        ("that's correct", {"pos_confirm": "correct"}),
        ("that's right", {"pos_confirm": "right"}),
        ("end the conversation", {"pos_confirm": "end"})
    ]
    negative_examples = [
        "keep talking",
        "no that's wrong",
        "that's not what I said"
    ]

class ComplaintClarificationTemplate(RegexTemplate):
    """Match user asking a clarification question"""
    slots = {
        "clarifying_question": word_lists.COMPLAINT_CLARIFY
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{clarifying_question}" + OPTIONAL_TEXT_POST,
        "what",
        "repeat",
        "pardon me",
    ]
    positive_examples = [
        ("what", {}),
        ("what do you mean alexa", {"clarifying_question": "what do you mean"}),
        ("what are you saying", {"clarifying_question": "what are you saying"}),
        ("what did you just say", {"clarifying_question": "what did you just say"}),
        ("could you please repeat yourself", {"clarifying_question": "could you please repeat"}),
        ("alexa can you ask me that again", {"clarifying_question": "can you ask me that again"}),
        ("repeat what you just said", {"clarifying_question": "repeat what you just said"}),
        ("i don't understand what you mean", {"clarifying_question": "don't understand what you mean"}),
        ("i do not know what you're talking about", {"clarifying_question": "do not know what you're talking about"}),
        ("i don't know what you're talking about", {"clarifying_question": "don't know what you're talking about"}),
        ("i said i don't know what you're talking about", {"clarifying_question": "don't know what you're talking about"}),
        ("i actually love nap so i don't know what you're talking about", {"clarifying_question": "don't know what you're talking about"}),
        ("i don't really know what you're talking about", {"clarifying_question": "don't really know what you're talking about"}),
        ("i don't know i think i lost you i don't know what you're talking about", {"clarifying_question": "don't know what you're talking about"}),
        ("you maybe hearing in the background i don't know what you're talking about", {"clarifying_question": "don't know what you're talking about"}),
        ("i still don't know what you're talking about", {"clarifying_question": "still don't know what you're talking about"}),
        ("okay he call me i don't know what you're talking about", {"clarifying_question": "don't know what you're talking about"}),
        ("yea i don't know what you're talking about", {"clarifying_question": "don't know what you're talking about"}),
        ("i do not know what you're talking about", {"clarifying_question": "do not know what you're talking about"}),
        ("i honestly don't even know what you're talking about", {"clarifying_question": "don't even know what you're talking about"}),
        ("i don't even know what you're talking about", {"clarifying_question": "don't even know what you're talking about"}),
        ("i never gonna call it before so i knew i have no idea what you're talking about", {"clarifying_question": "no idea what you're talking about"}),
        ("i really don't know what you're talking about", {"clarifying_question": "really don't know what you're talking about"}),
        ("the youtuber infinite otherwise i have no idea what you're talking about", {"clarifying_question": "no idea what you're talking about"}),
        ("i have no idea what you're talking about", {"clarifying_question": "no idea what you're talking about"}),
        ("no idea what you're talking about", {"clarifying_question": "no idea what you're talking about"}),
        ("i said i don't know what do i don't know what you're talking about", {"clarifying_question": "don't know what you're talking about"}),
        ("i don't really care i don't know what you're talking about", {"clarifying_question": "don't know what you're talking about"}),
        ("i was never gonna call it before so i knew i have no idea what you're talking about", {"clarifying_question": "no idea what you're talking about"}),
        ("who was what are you talking about", {"clarifying_question": "what are you talking about"}),
        ("who are you talking about", {"clarifying_question": "who are you talking about"}),
        ("i just said i like unicorns what are you talking about", {"clarifying_question": "what are you talking about"}),
        ("what are you talking about", {"clarifying_question": "what are you talking about"}),
        ("what are we talking about", {"clarifying_question": "what are we talking about"}),
        ("what the hell are you talking about", {"clarifying_question": "what the hell are you talking about"}),
        ("who do you talking about", {"clarifying_question": "who do you talking about"}),
        ("what the fuck are you talking about", {"clarifying_question": "what the fuck are you talking about"}),
        ("i don't know what you talking about", {"clarifying_question": "don't know what you talking about"}),
        ("what is what are you talking about", {"clarifying_question": "what are you talking about"}),
        ("i like to launch me because wait which to what are you talking about", {"clarifying_question": "which to what are you talking about"}),
        ("how long what you talking about", {"clarifying_question": "what you talking about"}),
        ("no i don't i don't know understand who is that who are you talking about", {"clarifying_question": "who are you talking about"}),
        ("do you have a confused i don't know what are you talking about", {"clarifying_question": "what are you talking about"}),
        ("i don't have any idea what you're talking about", {"clarifying_question": "any idea what you're talking about"}),
        ("yes why are you talking about", {"clarifying_question": "why are you talking about"}),
        ("what nonsense are you talking about", {"clarifying_question": "what nonsense are you talking about"}),
        ("what you talk about", {"clarifying_question": "what you talk about"}),
        ("what did you talk about", {"clarifying_question": "what did you talk about"}),
        ("i'm talking about the moon what are you talking about", {"clarifying_question": "what are you talking about"}),
        ("what did you chat about", {"clarifying_question": "what did you chat about"}),
        ("what game are you talking about", {"clarifying_question": "what game are you talking about"}),
        ("which lionking are you talking about", {"clarifying_question": "which lionking are you talking about"}),
        ("what series are you talking about", {"clarifying_question": "what series are you talking about"}),
        ("which avengers are avengers are you talking about", {"clarifying_question": "which avengers are avengers are you talking about"}),
        ("which home before dark are you talking about", {"clarifying_question": "which home before dark are you talking about"}),
        ("i don't know what the heck are you talking about", {"clarifying_question": "don't know what the heck are you talking about"}),
        ("i don't understand what you're saying", {"clarifying_question": "don't understand what you're saying"}),
        ("that was very wordy, i don't follow", {"clarifying_question": "i don't follow"}),
        ("no i hate school what are you talking about", {"clarifying_question": "what are you talking about"}),
        ("pardon me", {}),
        ("but we were talking about my sister", {"clarifying_question": "but we were talking about"}),
        ("i have no idea what you're talking about", {"clarifying_question": "no idea what you're talking about"}),
        ("say that again", {"clarifying_question": "say that again"}),
        ("alexa say that again please", {"clarifying_question": "say that again"}),
    ]
    negative_examples = [
        "what is your favorite color", 
        "let's talk about something else",
        "what do you want to talk about", 
        "i don't know what to talk about",
        "let's talk about something else",
        "let's talk about",
        "talk about",
        "i wanna talk about",
        "can we talk about",
        "what do you wanna talk about",
        "can you talk about",
        "no let's talk about",
        "we need to talk about",
        "what do you know about",
        "yes i want to talk about",
        "do you know about",
        "what else you want to talk about",
        "i don't know what i want to talk about"
    ]

class ComplaintMisheardTemplate(RegexTemplate):
    """Match user saying Alexa misheard them"""
    slots = {
        "misheard": word_lists.COMPLAINT_MISHEARD
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{misheard}" + OPTIONAL_TEXT_POST,
        "i asked" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("alexa that's not what i said", {"misheard": "not what i said"}),
        ("no i said corona virus", {"misheard": "no i said"}),
        ("you're not listening to me", {"misheard": "you're not listening"}),
        ("i didn't say that", {"misheard": "i didn't say"}),
        ("you are not hearing me", {"misheard": "you are not hearing"}),
        ("i didn't mean that", {"misheard": "i didn't mean"}),
        ("that's not what i said", {"misheard": "not what i said"}),
        ("alexa you didn't listen", {"misheard": "you didn't listen"}),
        ("no that's not what i said", {"misheard": "not what i said"}),
        ("i think you misheard me", {"misheard": "misheard me"}),
        ("no you heard me wrong", {"misheard": "heard me wrong"}),
        ("i asked what your favorite color is", {}),
        ("do you remember what we were talking about", {"misheard": "do you remember what we were talking about"}),
        ("that's not what i'm talking about", {"misheard": "not what i'm talking about"}),
        ("you don't even know what i'm talking about", {"misheard": "you don't even know what i'm talking about"}),
        ("that's not who i was talking about", {"misheard": "that's not who i was talking about"}),
        ("i that is not the 1 i was talking about", {"misheard": "that is not the 1 i was talking about"})
    ]
    negative_examples = [
        "i didn't hear you",
        "i said that i like dogs",
        "That's what i said",
        "i already said that",
        "you're listening to me",
        "you're hearing me",
        "i think you heard me",
        "you heard that correctly"
    ]

class ComplaintRepetitionTemplate(RegexTemplate):
    """Match user saying Alexa is repeating itself"""
    slots = {
        "repetition": word_lists.COMPLAINT_REPETITION
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{repetition}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("you asked me that before", {"repetition": "you asked me that before"}),
        ("you said that already", {"repetition": "you said that already"}),
        ("you already told me that", {"repetition": "you already told"}),
        ("alexa stop repeating yourself", {"repetition": "stop repeating"}),
        ("alexa you are repeating the same thing", {"repetition": "you are repeating"}),
        ("you keep saying that", {"repetition": "you keep saying"}),
        ("you just told me that", {"repetition": "you just told"}),
        ("you asked me the same thing earlier", {"repetition": "you asked me the same thing earlier"}),
        ("we already talked about cats", {"repetition": "we already talked about"})
    ]
    negative_examples = [
        "you never said that",
        "you didn't say that before",
        "could you repeat that",
        "please say that again",
        "what did you say earlier",
        "what did you just say"
    ]
    
class ComplaintPrivacyTemplate(RegexTemplate):
    slots = {
        "privacy": word_lists.COMPLAINT_PRIVACY
    }
    templates = [
        OPTIONAL_TEXT_PRE+"{privacy}"+OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("i don't want to tell you", {"privacy": "i don't want to tell"}),
        ("why did you ask me that", {"privacy": "why did you ask"}),
        ("none of your business", {"privacy": "none of your business"}),
        ("that's not your business alexa", {"privacy": "not your business"}),
        ("that's creepy. don't ask me that", {"privacy": "don't ask me"}),
        ("i'm not going to tell you my name", {"privacy": "i'm not going to tell you"}),
        ("i'm not telling you that", {"privacy": "i'm not telling you"}),
    ]
    negative_examples = [
        "i want to tell you",
        "what is a small business",
        "what did you ask me",
        "repeat what you asked me",
        "can you ask me what my favorite color is",
        "i want to tell you my favorite color"
    ]     

# Various templates for CATEGORY RG to reponse to shorter user responses

WHAT_ABOUT_YOU_EXPRESSIONS = [
    "(what|how) about (you|you.|you?)",
]

class WhatAboutYouTemplate(RegexTemplate):
    slots = {
        'what_about_you': WHAT_ABOUT_YOU_EXPRESSIONS
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{what_about_you}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ('i honestly don\'t know. what about you. what do you like', {'what_about_you': 'what about you.'}),
        ('i don\'t quite know. how about you?', {'what_about_you': "how about you?"}),
        ("what about you alexa", {'what_about_you': 'what about you'}),
        ("what about you.", {'what_about_you': 'what about you.'}), 
        ("what about you alexa. I don't really remember", {'what_about_you': "what about you"}),
        ("I don't actually remember. how about you alexa", {'what_about_you': "how about you"}),
    ]
    negative_examples = [
        'i know',
        'what did you just say'
    ]

RESPONSE_TO_WHAT_ABOUT_YOU = [
    "I like so many different ones that it can be hard to answer my own questions!",
    "Good question! I have a hard time choosing!",
    "I'm not really sure. I can't make up my mind!"
    "It's always hard for me to pick!",
    "I like so many! It's hard to give just one answer.",
    "I can never pick because I like so many."
]

DONT_KNOW_EXPRESSIONS = [
    'don(\')?t (really |actually |quite )?know',
    'not (really |quite )?know',
    'not (really |so |quite )?sure',
    'no idea',
    "don't (really |actually |quite )?remember"
]

class DontKnowTemplate(RegexTemplate):
    slots = {
        'dont_know': DONT_KNOW_EXPRESSIONS
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{dont_know}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ('i honestly don\'t know', {'dont_know': 'don\'t know'}),
        ('i don\'t quite know', {'dont_know': "don't quite know"}),
        ("i don't know", {'dont_know': 'don\'t know'}),
        ("I'm not sure", {'dont_know': 'not sure'}), 
        ("I don't really remember", {'dont_know': "don't really remember"}),
        ("I don't actually remember", {'dont_know': "don't actually remember"}),
        ("I'm really not sure", {'dont_know': "not sure"}),
        ("I don't remember", {'dont_know': "don't remember"}),
        ("I really don't know", {'dont_know': 'don\'t know'})
    ]
    negative_examples = [
        'i know',
    ]

# TODO: do we want to condition on the category, on the question?
RESPONSE_TO_DONT_KNOW = [
    "No worries that was a hard question!",
    "Yeah a lot of people find it hard to answer that question too.",
    "That's ok! It's a tough question."
]

BACK_CHANNELING_EXPRESSION = [
    '(that\'s |that )?cool',
    'yeah',
    'okay',
    'yes',
    'nice'
] 

class BackChannelingTemplate(RegexTemplate):
    slots = {
        'ok': BACK_CHANNELING_EXPRESSION
    }
    templates = [
        "{ok}"
    ]
    positive_examples = [
        ("that's cool", {'ok': "that's cool"}),
        ('cool', {'ok': "cool"}),
        ("okay", {'ok': 'okay'}),
    ]
    negative_examples = [
        'i know',
    ]

RESPONSE_TO_BACK_CHANNELING = [
    "I know right!",
    "Yeah!"
]

EVERYTHING_EXPRESSIONS = [
    "a lot of",
    "lots of",
    "many",
    "everything", 
]

class EverythingTemplate(RegexTemplate):
    slots = {
        'everything': EVERYTHING_EXPRESSIONS
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{everything}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("I like everything", {'everything': "everything"}),
        ('I like a lot of things', {'everything': "a lot of"}),
    ]
    negative_examples = [
        'i love pasta'
    ]

RESPONSE_TO_EVERYTHING_ANS = [
    "Yeah it is always hard to pick!",
    "A lot of people also find it is hard to pick!",
]

NOTHING_EXPRESSIONS = [
    "nothing",
    "none",
    "don(\')?t have one", 
    "don(\')?t have a (favorite|favourite)",
    "nobody",
]

class NotThingTemplate(RegexTemplate):
    slots = {
        'not_thing': NOTHING_EXPRESSIONS
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{not_thing}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("I like nothing", {'not_thing': "nothing"}),
        ("I don't have one", {'not_thing': "don't have one"}),
        ("I don't have a favorite", {'not_thing': "don't have a favorite"})
    ]
    negative_examples = [
        'i like pasta'
    ]

RESPONSE_TO_NOTHING_ANS = [
    "No worries!",
    "That\'s alright.",
]

# Demonstration of how to use RegexTemplates:
if __name__ == "__main__":

    # Create template
    template = MyNameIsTemplate()

    # See output of template on an example
    slots = template.execute('my name is abi')
    print(slots)

    # Run the template's tests
    template.test_examples()
