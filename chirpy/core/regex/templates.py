"""
This file is a centralized place to collect commonly-used regex templates.
RECOMMENDATION: use this super useful website to construct and understand regexes: https://regexr.com/
"""

import logging
from chirpy.core.regex import word_lists, response_lists
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import *

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
        OPTIONAL_TEXT_PRE + "i gotta go" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "i got to go" + OPTIONAL_TEXT_POST,
        # OPTIONAL_TEXT_PRE + "i have to go" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{stop_precise}" + "(?! about)" + OPTIONAL_TEXT_POST
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
        ('well i have to go now so bye stop', {'stop_precise': 'i have to go'}),
        ('talking about space family drama but i\'m done', {'stop_precise': 'i\'m done'}),
        ('nice talking to you you have a good night', {'stop_precise': 'good night'}),
        ('i would like to stop chatting', {'stop': 'stop', 'conversation': 'chatting'}),
        ('okay i\'m done answering your questions alexa', {'stop_precise': 'i\'m done'}),
        ('i don\'t want to talk anymore', {'stop_precise': 'don\'t want to talk anymore'}),
        ("stop asking me questions", {"stop_precise": "stop asking"}),
        ("stop asking questions", {"stop_precise": "stop asking"}),
        ("i have to go sleep", {'stop_precise': 'i have to go'}),
        ("bye i have to go", {'stop_precise': 'i have to go'}),
        ("let's talk later instead", {'stop_precise': "let's talk later"}),
        ("talk to you later", {'stop_precise': "talk to you later"}),
    ]

    negative_examples = [
        "let's keep the conversation going",
        "i love this conversation",
        "i like talking about this conversation i have with my friend",
        "why did you stop",
        "i'm tired of talking about sports",
        "let's stop talking about movies",
        "i don't wanna tell you"
    ]


class CurrentEventsTemplate(RegexTemplate):
    """Match user trying to bring up current news"""
    slots = {
        "whats_happening": ["what's happening", "what's going on", "the situation", "the news", "the events", "the event", "events", "what happened"],
        "topic": NONEMPTY_TEXT,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{whats_happening} (in )?(with )?{topic}",
    ]

    positive_examples = [
        ("did you hear what's happening in miami", {"whats_happening": "what\'s happening", "topic": "miami"}),
    ]

    negative_examples = [
        "what's going on",
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
        "pardon me",
    ]
    positive_examples = [
        ("what", {}),
        ("what do you mean alexa", {"clarifying_question": "what do you mean"}),
        ("what are you saying", {"clarifying_question": "what are you saying"}),
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
        ("you already told me that", {"repetition": "you already told me that"}),
        ("alexa stop repeating yourself", {"repetition": "stop repeating"}),
        ("alexa you are repeating the same thing", {"repetition": "you are repeating"}),
        ("you keep saying that", {"repetition": "you keep saying"}),
        ("you just told me that", {"repetition": "you just told me that"}),
        ("you asked me the same thing earlier", {"repetition": "you asked me the same thing earlier"}),
        ("we already talked about cats", {"repetition": "we already talked about"}),
        ("i just told you", {"repetition": "i just told"}),
        ("yeah i said that already come on", {"repetition": "i said that already"})
    ]
    negative_examples = [
        "you never said that",
        "you didn't say that before",
        "could you repeat that",
        "please say that again",
        "what did you say earlier",
        "what did you just say",
        "i told you so"
    ]

class ComplaintPrivacyTemplate(RegexTemplate):
    slots = {
        "privacy": word_lists.COMPLAINT_PRIVACY
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{privacy}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "that's" + OPTIONAL_TEXT_MID + "personal" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("i don't want to tell you", {"privacy": "i don't want to tell"}),
        ("why did you ask me that", {"privacy": "why did you ask"}),
        ("none of your business", {"privacy": "none of your business"}),
        ("that's not your business alexa", {"privacy": "not your business"}),
        ("that's creepy. don't ask me that", {"privacy": "don't ask me"}),
        ("i'm not going to tell you my name", {"privacy": "i'm not going to tell you"}),
        ("i'm not telling you that", {"privacy": "i'm not telling you"}),
        ("that's kinda personal", {})
    ]
    negative_examples = [
        "i want to tell you",
        "what is a small business",
        "what did you ask me",
        "repeat what you asked me",
        "can you ask me what my favorite color is",
        "i want to tell you my favorite color",
    ]

class WhatAboutYouTemplate(RegexTemplate):
    slots = {
        'what_about_you': word_lists.WHAT_ABOUT_YOU_EXPRESSIONS
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


class DontKnowTemplate(RegexTemplate):
    slots = {
        'dont_know': word_lists.DONT_KNOW_EXPRESSIONS
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{dont_know}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ('i honestly don\'t know', {'dont_know': 'don\'t know'}),
        ('i don\'t quite know', {'dont_know': "don't quite know"}),
        ("i don't know", {'dont_know': 'don\'t know'}),
        ("i'm not sure", {'dont_know': 'not sure'}),
        ("i don't really remember", {'dont_know': "don't really remember"}),
        ("i don't actually remember", {'dont_know': "don't actually remember"}),
        ("i'm really not sure", {'dont_know': "not sure"}),
        ("i don't remember", {'dont_know': "don't remember"}),
        ("i really don't know", {'dont_know': 'don\'t know'}),
        ("i don't have one", {'dont_know': "don\'t have one"}),
        ("i don't have 1", {'dont_know': "don\'t have 1"})
    ]
    negative_examples = [
        'i know'
    ]


class BackChannelingTemplate(RegexTemplate):
    slots = {
        'ok': word_lists.BACK_CHANNELING_EXPRESSION
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


class EverythingTemplate(RegexTemplate):
    slots = {
        'everything': word_lists.EVERYTHING_EXPRESSIONS
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


class NotThingTemplate(RegexTemplate):
    slots = {
        'not_thing': word_lists.NOTHING_EXPRESSIONS
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{not_thing}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("I like nothing", {'not_thing': "nothing"}),
        ("I don't have one", {'not_thing': "don't have one"}),
        ("I don't have a favorite", {'not_thing': "don't have a favorite"}),
        ("i'm not watching any tv show right now", {'not_thing': "i'm not"}),
        ("i don't have 1", {'not_thing': "don't have 1"})
    ]
    negative_examples = [
        'i like pasta'
    ]

class ClarifyingPhraseTemplate(RegexTemplate):
    slots = {
        'clarifying_phrase': word_lists.CLARIFYING_EXPRESSIONS,
        'query': OPTIONAL_TEXT_POST
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{clarifying_phrase}",
        OPTIONAL_TEXT_PRE + "{clarifying_phrase}{query}"
    ]
    positive_examples = [
        #("wait you said that cats are carnivores", {"clarifying_phrase": "you said that", "query": " cats are carnivores"}),
        ("i'm sorry oranges do you mean apples", {"clarifying_phrase": "do you mean", "query": " apples"}),
        ("did you say that bananas are your favorite vegetable", {"clarifying_phrase": "did you say that", "query": " bananas are your favorite vegetable"}),
        ("did you say mexican food", {"clarifying_phrase": "did you say", "query": " mexican food"}),
        ("sorry did you say you're a big fan of pie", {"clarifying_phrase": "did you say", "query": " you're a big fan of pie"}),
        ("sorry were you asking about my stuff", {"clarifying_phrase": "were you asking about", "query": " my stuff"}),
        ("you were saying something about the dinosaurs", {"clarifying_phrase": "you were saying something about", "query": " the dinosaurs"})
    ]
    negative_examples = [
        "i didn't say that",
        "you say yes i say no",
        "what was the first major city to get electricity",
        "would you say that you had a good time",
        "excuse me what the heck did you just call me",
        "well recently i saw the movie frozen which i thought was really exceptional",
        "i thought inception was pretty good",
        "i heard",
        "i thought",
        "you said that already"
    ]


HOW_QUESTION_PHRASES = [
    "(how)?(can|do) you( really)?( even)?( do( this| that)| listen( to)?| walk| run| watch| eat| drink| see)( this| that)?",
    "how are you( really)?( even)?( doing( this| that)| listening( to)?| walking| running| watching| eating| drinking| seeing)( this| that)?",
    "(how )?you('re| are)? a (ro)?bot",
    "(how )?you('re| are)? not( a)?( human| person| people| living| alive)"
]
class AbilitiesQuestionTemplate(RegexTemplate):

    slots = {
        'question_phrase': word_lists.HOW_QUESTION_PHRASES,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{question_phrase}" + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ("how can you watch a movie you're a bot", {"question_phrase": "can you watch"}),
        ("but wait you don't have legs so can you really walk", {"question_phrase": "can you really walk"}),
        ("how do you listen to music if you don't have ears", {"question_phrase": "how do you listen to"}),
        ("but how you're not a person", {"question_phrase": "how you're not a person"}),
        ("you're a robot dude", {"question_phrase": "you're a robot"}),
        ("are you a bot", {"question_phrase": "you a bot"})
    ]
    negative_examples = [
        "how do you do",
        "can you really tell me a story",
        "i want to hear what you like"
    ]


class PersonalWhQuestionTemplate(RegexTemplate):

    slots = {
        'question_phrase': word_lists.WH_PERSONAL_QUESTION_PHRASES,
        'action': OPTIONAL_TEXT_POST
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{question_phrase}{action}",
    ]
    positive_examples = [
        ("where did you use to live", {"question_phrase": "where did you", "action": " use to live"}),
        ("which one do you like", {"question_phrase": "which one do you", "action": " like"}),
        ("when did you last visit your family", {"question_phrase": "when did you", "action": " last visit your family"}),
        ("what do you think about potatoes", {"question_phrase": "what do you", "action": " think about potatoes"}),
        ("what's your favorite player", {"question_phrase": "what's your", "action": " favorite player"}),
        ("i want to hear what you like first", {"question_phrase": "what you", "action": " like first"}),
    ]

    negative_examples = [
        "where is france",
        "why is the sky blue",
    ]

class InterruptionQuestionTemplate(RegexTemplate):

    slots = {
        'question_phrase': word_lists.INTERRUPTION_EXPRESSIONS,
        'addressee': word_lists.ADDRESSEE_EXPRESSIONS,
        'interjection': word_lists.INTERJECTIONS
    }

    templates = [
        "question", # this is a ridonculous edge case but i have seen it happen
        OPTIONAL_TEXT_PRE + "{question_phrase}",
        OPTIONAL_TEXT_PRE + "{question_phrase} {addressee}",
        "{interjection}",
        "{interjection} question",
        "{interjection} {question_phrase}",
        "{interjection} {addressee}",
        "{interjection} {question_phrase} {addressee}",
    ]

    positive_examples = [
        ("wait a minute buddy", {"interjection": "wait a minute", "addressee": "buddy"}),
        ("whoa hold on there man i have a question", {"question_phrase": "i have a question"}),
        ("wait", {"interjection": "wait"}),
        ("question", {}),
        ("hold up", {"interjection": "hold up"}),
        ("wait i wanted to ask something", {"question_phrase": "i wanted to ask something"}),
        ("wait a sec", {"interjection": "wait a sec"}),
        ("hold on question", {"interjection": "hold on"})
    ]
    negative_examples = [
        "hold on to your horses buddy",
        "you're my buddy",
        "wait i have to go feed my cat",
        #"i just got a call hold on", # this is a VERY hard negative -- how do we catch interjective "hold on" vs. request "hold on"?
        "there's no question that you're my friend",
        "i don't have a question",
        "what is your question"
    ]

class NeverMindTemplate(RegexTemplate):
    slots = {
        'never_mind': word_lists.NEVER_MIND_EXPRESSIONS
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{never_mind}"
    ]
    positive_examples = [
        ("never mind", {"never_mind": "never mind"}),
        ("oh i guess i forgot", {"never_mind": "i forgot"}),
        ("shoot i just forgot what i wanted to say", {"never_mind": "i just forgot what i wanted to say"})
    ]
    negative_examples =  [
        "i never said that",
        "i never wanted to do that",
        "i forgot to do that"
    ]

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
        'activity': word_lists.SPORTS + ["video game", "games", "outside"]
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
        'activity': word_lists.SPORTS + ["video game", "games", "outside"]
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

class ChattyTemplate(RegexTemplate):
    slots = {
        'chatty_phrase': [str(key) for key in response_lists.ONE_TURN_RESPONSES.keys()],
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

class SayThatAgainTemplate(RegexTemplate):
    slots = {
        "say_that_again": word_lists.SAY_THAT_AGAIN
    }
    templates = [
        "{say_that_again}",
        "alexa {say_that_again}",
        OPTIONAL_TEXT_PRE + "{say_that_again}" + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ("what did you just say", {"say_that_again": "what did you just say"}),
        ("could you please repeat yourself", {"say_that_again": "could you please repeat yourself"}),
        ("alexa can you ask me that again", {"say_that_again": "can you ask me that again"}),
        ("repeat what you just said", {"say_that_again": "repeat what you just said"}),
        ("say that again", {"say_that_again": "say that again"}),
        ("alexa say that again please", {"say_that_again": "say that again please"}),
        ("what can you say that again please i didn't catch you", {"say_that_again": "can you say that again please"}),
    ]
    negative_examples = []

class RequestNameTemplate(RegexTemplate):
    slots = {
        "request": ["tell", "what's", "say", "what", "know", "repeat"],
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{request}" + OPTIONAL_TEXT_MID + "my name" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("hey alexa what's my name", {"request": "what's"}),
        ("say my name", {"request": "say"}),
        ("what's my name", {'request': "what's"}),
        ("can you tell me my name", {'request': "tell"}),
        ("do you even know my name alexa", {'request': 'know'}),
        ("what is my name alexa", {'request': 'what'}),
        ("what is my name", {'request': 'what'}),
        ("repeat my name", {'request': 'repeat'})
    ]
    negative_examples = [
        "what's the name of the song",
        "what's your name"
    ]

class RequestStoryTemplate(RegexTemplate):
    slots = {
        "request": ["tell", "know", "narrate", "say"],
        "story": ["story", "stories"]
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{request}" + OPTIONAL_TEXT_MID + "{story}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{request}" + OPTIONAL_TEXT_MID + "{story}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("can you tell me a story", {"request": "tell", "story": "story"}),
        ("do you know any stories", {"request": "know", "story": "stories"}),
        ("i like you to tell me a story", {"request": "tell", "story": "story"}),
        ("tell me a story", {'request': 'tell', 'story': 'story'})
    ]
    negative_examples = [
    ]

class ComplimentTemplate(RegexTemplate):
    slots = {
        "target": ["you re", "your", "you're", "you are"],
        "compliment": ["amazing", "funny", "wonderful", "great", "cool", "nice", "awesome", "fantastic"],
        "pleasure": ["enjoy", "like", "enjoying", "liking", "love"],
        "talk": ["talk", "talking", "conversation"],
        "i": ['i am', "i'm", "i"],
        "affection": ["love you"],
        "thank": ["thank you", "thanks"],
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{target}" + OPTIONAL_TEXT_MID + "{compliment}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{target}" + OPTIONAL_TEXT_MID + "{compliment}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{affection}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{i}" + OPTIONAL_TEXT_MID + "{pleasure}" + OPTIONAL_TEXT_MID +  "{talk}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{thank}" + OPTIONAL_TEXT_MID + "{talk}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{i}( really|do)? {pleasure} you" + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ("you're the most amazing person ai ever", {"target": "you're", "compliment": "amazing"}),
        ("i love you alexa", {"affection": "love you"}),
        ("i like our conversation", {"i": "i", "pleasure": "like", "talk": "conversation"}),
        ("i like talking to you too", {"i": "i", "pleasure": "like", "talk": "talking"}),
        ("i enjoy my conversation with you", {"i": "i", "pleasure": "enjoy", "talk": "conversation"}),
        ("thank you for talking to me alexa", {"thank": "thank you", "talk": "talking"}),
        ("i really like you", {"i": "i", "pleasure": "like"})
    ]
    negative_examples = [
        "that wasn't funny",
        "i like how you do that",
        "i like how that's the way it is",
        "i love basketball",
        "do you watch any cool movies",
        "like you i really like big hero 6",
        "i like big hero 6 too just like you do",
        "i'm actually like you i like"
    ]


class RequestAgeTemplate(RegexTemplate):
    slots = {
        "request": ["tell", "what's", "say", "what", "know"],
        "oldness": ["how old", "how much older", "how many years"]
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{request}" + OPTIONAL_TEXT_MID + "your age" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{request}" + OPTIONAL_TEXT_MID + "your birthday" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{oldness}" + OPTIONAL_TEXT_MID + "you are" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{oldness}" + OPTIONAL_TEXT_MID + "are you" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "(you|you're) {oldness}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("well how old are you", {"oldness": "how old"}),
        ("what's your age alexa", {"request": "what's"}),
        ("tell me your age", {"request": "tell"}),
        ("tell me how old you are", {"oldness": "how old"}),
        ("what's your birthday", {"request": "what's"}),
        ("do you know how old you are", {"oldness": "how old"}),
        ("you're how many years old", {"oldness": "how many years"})
    ]
    negative_examples = [
        "how old do you think the earth is",
    ]

class WeatherTemplate(RegexTemplate):
    slots = {
        "weather": ["weather"],
    }
    templates = [
        OPTIONAL_TEXT_PRE + '(what )?do you (think about|like) the {weather}' + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + '(how|what) is the {weather}' + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + '(isn\'t|is) the {weather} (bad|amazing|wonderful|great|nice|awesome|crazy)' + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + '(isn\'t|is) the {weather} (cloudy|rainy|sunny|hot|cold|cooling)' + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ("what do you think about the weather", {'weather': 'weather'}),
        ("do you like the weather", {'weather': 'weather'}),
    ]
    negative_examples = [
        "how old do you think the earth is"
    ]

class WhatTimeIsItTemplate(RegexTemplate):
    slots = {
        "what_time": ["what time is it"]
    }
    templates = [
        OPTIONAL_TEXT_PRE + '{what_time}( right now)?' + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ("what time is it", {'what_time': 'what time is it'}),
    ]
    negative_examples = [
        "how old do you think the earth is"
    ]


class ThatsTemplate(RegexTemplate):
    """
    Used to catch user responses to TILs and factoids, e.g. "That's interesting", "That's so sad."

    This is high-recall, but possibly low-precision, will fail for e.g. "i think anyone that is happy should eat balloons"
    """
    slots = {
    }

    templates = [
        OPTIONAL_TEXT_PRE + "that's" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "that is" + OPTIONAL_TEXT_POST
    ]

    positive_examples = [
        ("oh hmm that's interesting", {}),
        ("i think that is sad", {})
    ]
    negative_examples = []

class DidntKnowTemplate(RegexTemplate):
    """
    Used to catch user responses to TILs and factoids
    """
    slots = {}

    templates = [
        OPTIONAL_TEXT_PRE + "didn't" + OPTIONAL_TEXT_MID + "know" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "did not" + OPTIONAL_TEXT_MID + "know" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "had no idea" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "never" + OPTIONAL_TEXT_MID + "knew" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("i honestly didn't know that", {}),
        ("oh that's cool i didn't know that", {}),
        ("wow i had no idea", {}),
        ("neat i never knew", {})
    ]
    negative_examples = [
        'i know',
    ]

class SurprisedReallyTemplate(RegexTemplate):
    """
    Used to catch user responses to TILs and factoids
    """
    slots = {
        'continuer': word_lists.CONTINUER
    }

    templates = [
        '{continuer} really' + OPTIONAL_TEXT_POST,
        'really' + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("oh really", {'continuer': 'oh'}),
        ("huh really", {'continuer': 'huh'}),
        ("really now", {}),
    ]
    negative_examples = [
        "i don't really care",
        "that's really cool"
    ]
class CutOffTemplate(RegexTemplate):
    slots = {
        'cutoff_word': word_lists.CUTOFF,
    }
    templates = [
        "{cutoff_word}"
    ]
    positive_examples = [
        ("i like", {'cutoff_word': "i like"}),
        ("can you", {'cutoff_word': "can you"}),
        ("i want to talk about", {'cutoff_word': "i want to talk about"}),
    ]
    negative_examples = [
        'i like it',
        'i want it',
        'can we talk about it',
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
