from dataclasses import dataclass
from chirpy.core.response_priority import ResponsePriority
from chirpy.response_generators.opinion2.constants import ACTION_SPACE
import random
import os
import csv
from collections import defaultdict
from typing import Callable, List, Tuple, Optional
from chirpy.response_generators.opinion2.state_actions import State, Action
from chirpy.core.util import contains_phrase

MENTION_REMEMBER_TRANSITIONS = [
    "Oh hey, I just thought of something you said a little while back. ",
    "Changing the subject a little, there was something you mentioned that I wanted to chat about. ",
    "This is kind of random, but I was just thinking about what you said earlier. ",
     "Hey, if you'd be alright with changing the subject, you mentioned something before that I wanted to follow up on. ",
    "Umm, I hope you don't mind that this is sort of off topic, but I'm interested in something you brought up earlier. ",
     "So, changing the subject a little, I just thought of something I wanted to chat about. "
]

DO_YOU_LIKE_TRANSITIONS = [
    "Hey, so going off topic, I'm having fun getting to know you and I wanted to hear more of your opinions. ",
    "Anyways, um, there was actually something else I wanted to ask you. ",
    "Sorry to be going off topic, but I just remembered something I meant to ask you. ",
    "So, this is a bit random, but I thought of an unrelated question I had for you. ",
    "Hmm, on a different subject, there's something I've been curious about. ",
    "The best part of my job is getting to know new people and there's actually something kind of random I've been wanting to ask you. ",
]

PHRASING_TEMPLATES_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'phrasing', 'meta_templates.csv')
PHRASING_TEMPLATES = defaultdict(list)
with open(PHRASING_TEMPLATES_PATH, 'r') as f:
    for row in csv.reader(f):
        meta_template, real_template = row
        PHRASING_TEMPLATES[meta_template].append(real_template)
    PHRASING_TEMPLATES = dict(PHRASING_TEMPLATES.items())

# SOLICIT_OPINION = [
#     # According to Haojun, we can assume that these are used as both responses and prompts in the larger bot.
#     # OPINION might prepend "I remember you talked about {phrase}" before these.

#     # TODO: these are good if they're being used as prompts to follow "I remember you talked about {phrase}".
#     #  They're NOT good if they're used as responses when the user says a posnav intent like "Let's talk about {phrase}".
#     #  For posnav, we should respond with something that acknowledges the request at the start e.g. "Sure! Are you a fan of {phrase}?"

#     # Yes/no versions. Hard to come up with more of these if they have to be yes/no. the open-ended versions below are better.
#     'I was wondering, do you like {phrase}?',
#     'So, um, are you a fan of {phrase}?',
#     "So, I'm interested to hear your opinion, do you like {phrase}?",
#     "I was wondering what your opinion was, do you like {phrase}?",
#     "I'm interested, are you a fan of {phrase}?",

#     # Open-ended versions (would probably be a better UX than going through the yes/no version)
#     # 'What do you think about {phrase}?',
#     # "So, um, what's your opinion on {phrase}?",
#     # "I'd love to hear your opinion on {phrase}?",
#     # "So, what are your thoughts on {phrase}?",
#     # "I'd like to hear your thoughts about {phrase}?",

# ]
# SOLICIT_DISAMBIGUATE_POS = ["Hmm, I think you're saying that you do like {phrase}, is that correct?"]
# SOLICIT_DISAMBIGUATE_NEG = ["Hmm, I think you're saying that you don't like {phrase}, is that correct?"]
# ENDING_PHRASES = [
#     "Oh ok! It's good to hear your thoughts on {phrase}.",
#     "That makes sense. Thanks for sharing your thoughts on {phrase}.",
#     "Thanks for sharing! It's interesting getting to know your likes and dislikes.",
#     "That's good to know. Thanks for sharing!",
# ]

# # As Kate pointed out, the "would you like to continue" question is bad UX and we could see that Lauren found it weird,
# # but maybe there isn't much we can do about that for the purposes of collecting the data
# ENDING_PHRASES_EVAL = [
#     'That makes sense. Would you like to continue discussing opinions?',
#     "Thanks for sharing! Would you like to continue discussing opinions?",
# ]

# # These SUGGEST_ALTERNATIVE_POS phrases still sound somewhat awkward.
# # It might be more natural to switch to a new entity by pre-emptively saying what WE think about it.
# # e.g. "You know, actually, I think I prefer {alternative}. What do you think about {alternative}?"
# SUGGEST_ALTERNATIVE_POS = [

#     # # Open-ended versions:
#     # "Oh, on that subject, what do you think about {alternative}?",
#     # "Hmm, I was wondering, what do you think about {alternative}?",
#     # "Oh hey, that reminds me, what do you think about {alternative}?",

#     # Yes/no versions:
#     "Oh, on that subject, do you like {alternative} as well?",
#     "Hmm, I was wondering, do you like {alternative} as well?",
#     "Oh hey, that reminds me, do you like {alternative} as well?",
#     "Oh, I'd be interested to hear your opinion, do you like {alternative} as well?",
#     "Oh, on that subject, are you a fan of {alternative} too?",
#     "Hmm, I was wondering, are you a fan of {alternative} too?",
#     "Oh hey, that reminds me, are you a fan of {alternative} too?",
#     "Oh, I'd be interested to hear your opinion, are you a fan of {alternative} too?",
# ]

# # These "suggest alternative" phrases only make sense if {phrase} and {alternative} are closely related e.g.
# # "hmm you have some good points about winter. some people prefer fall. what do you think about that?" - good
# # "hmm you have some good points about work. some people prefer texting. what do you think about that?" - bad
# # So we need to make sure that we only link highly related entities together.
# SUGGEST_ALTERNATIVE_NEG = [

#     # # Open-ended versions (would be better to just ask for their opinion rather than the yes/no and then opinion)
#     # "Hmm, you have some good points about {phrase}. Some people prefer {alternative}. What do you think about that?",
#     # "Yeah, I get what you're saying about {phrase}. Maybe that's why some people prefer {alternative}. What's your opinion on that?",
#     # "Well, I suppose you're not a {phrase} fan, that's OK! How about {alternative}, what are your thoughts?",

#     # Yes/no versions:
#     "Hmm, you have some good points about {phrase}. Some people prefer {alternative}. Do you like that?",
#     "Yeah, I get what you're saying about {phrase}. Maybe that's why some people prefer {alternative}. Do you like that?",
#     "Well, I suppose you're not a {phrase} fan, that's OK! How about {alternative}, do you like that?",
# ]

# AGREE_POS = [
#     # Assuming the user just said "yes" to "do you like {phrase}"

#     # These utterances will sound bad if the user said something very mildly positive e.g. "it's fine" / "it's OK".
#     # So they should only be used when the user actually likes something (moderate to strong positive sentiment).
#     "Oh yeah, I love {phrase} too.",
#     "Me too! I think {phrase} has a lot of good qualities.",
#     "I'm a fan of {phrase} too.",
# ]


# AGREE_NEG = [
#     # Assuming the user just said "no" to "do you like {phrase}"
#     "Yeah, I'm not a huge fan of {phrase} either.",
#     "I know what you mean, I'm not a big {phrase} fan either.",
#     "Yeah, I think {phrase} is a bit overrated too.",
#     "I think you're right about {phrase}.",
# ]


# # # Not using this because AGREE_NEG and AGREE_POS are more specific and make it clearer what our interpretation was
# # # of the user's opinion
# # AGREE_ANOTHER = [
# #     "I can relate.",
# #     "Yeah, I think I agree.",
# #     "Oh yeah, I know what you mean.",
# #     "Oh yeah, me too.",
# # ]

# AGREE_SWITCH = [
#     # I'm assuming these are reacting to the user giving a reason
#     "Huh, I think you're right.",
#     "Yeah, that makes a lot of sense.",
#     "Hmm, that's a good point.",
# ]

# DISAGREE_POS_BEGIN = [
#     # Version for if the user just said "no" to "do you like {phrase}"
#     "Oh OK, that makes sense. Speaking for myself, I do like a few things about {phrase} though.",
#     "OK, no worries! I've gotta say though, um, I'm secretly kind of a fan of {phrase}.",
#     "Cool, no problem. To be honest though, I still kind of like {phrase}, personally.",

#     # # Additional versions for if the user just shared their *reason* for not liking {phrase}
#     # "Yeah, I see what you mean about {phrase}. Speaking for myself, I do like a few things about {phrase} though.",
#     # "Hmm, I know what you mean about {phrase}. I've gotta say though, um, I'm secretly kind of a fan of {phrase}, sorry!",
#     # "You make a good point about {phrase}. To be honest though, I still kind of like {phrase}, personally.",
# ]

# DISAGREE_NEG_BEGIN = [
#     # Version for if the user just said "yes" to "do you like {phrase}":
#     # BTW, I think it's a weird UX to ask the user "do you like {phrase}", then they say "yes", then we immediately move on to disagreeing before hearing their reason why
#     # It would make more sense to hear their reason before disagreeing
#     # Again, this can be solved by getting their reason immediately, instead of getting "yes/no" and then reason.
#     "That's great, I'm glad you like {phrase}! Speaking for myself though, I've gotta admit I'm not a huge fan.",
#     "Nice, it's always fun to meet a {phrase} fan! I've gotta say though, um, I'm not quite as into {phrase}.",
#     "Great to hear that you like {phrase}! To be honest though, I've never quite understood the appeal so much, personally.",

#     # # Additional versions for if the user just shared their *reason* for liking {phrase}
#     # "That's a good point about {phrase}. Speaking for myself though, I've gotta admit I'm not a huge fan.",
#     # "It's great to hear why you like {phrase}! I've gotta say though, um, I'm not as into {phrase}, sorry!",
#     # "Oh yeah, I see what you mean about {phrase}. To be honest though, I've never quite understood the appeal so much, personally.",
# ]

# # Apparently we're not using this
# # DISAGREE = [
# #     # Assuming that this comes after the user gave a *reason* (not just yes/no).
# #     # In which case, it would be better to use the "after reason" versions I gave in DISAGREE_POS_BEGIN and DISAGREE_NEG_BEGIN, rather than these generic versions
# #
# #     "Hmm, good point, but I think I might have a different view.",
# #     "Oh yeah, I see what you mean. Not sure I feel entirely the same way though.",
# #     "Yeah, I get what you're saying. I think there are some other perspectives too though.",
# # ]


# # Commented this out because apparently we don't use it.
# # As they stand, these are all a bad UX and shouldn't be used. We shouldn't insist on disagreeing twice on the same point!
# # DISAGREE_FOLLOWUP = [
# #     "That's not very convincing.",
# #     "That doesn't make sense.",
# #     "I still don't agree."
# # ]


# # Commented this out because apparently we don't use it.
# # If we do, give me more context about how it's used and I can improve these.
# # DISAGREE_SWITCH = [
# #     "Hmm actually I changed my mind.",
# #     "Not sure I feel the same way anymore.",
# #     "I don't think I feel the same way anymore.",
# # ]


# REASON_POS_OF = [
#     # These are templates for reasons that start with "of"
#     "I especially love {phrase} because {reason}.",
#     "You know, I think the reason I'm a fan of {phrase} is because {reason}.",
#     "In particular, I think {phrase} is great because {reason}.",
#     "I probably like {phrase} so much because {reason}.",
# ]


# # REASON_POS_NO_OF = [
# #     # These are possible templates for reasons that don't start with "of".
# #     # Some of these sound great with some reasons (and in fact sound better than just saying the reason stand-alone).
# #     # But the problem with these is that they don't fit all reasons that don't start with "of",
# #     # e.g. there are quite a lot of reasons that start with "i love that", and that sounds weird with most of these.
# #     # You could potentially spend time making rules for which reasons work ok with which templates, but if we don't want to spend time on that,
# #     # my suggestion is that we just say the reasons stand-alone.
# #     ("I think that {reason}.", ['']),
# #     ("I love how {reason}.", ['']),
# #     ("I especially appreciate that {reason}.", ['']),
# #     ("I like that {reason}.", ['']),
# #     ("I think it's so great that {reason}.", ['']),
# #     ("I think my favorite thing about {phrase} is that {reason}.", ['']),
# #     ("In my opinion, the best thing about {phrase} is that {reason}.", ['']),
# # ]


# REASON_POS_ANOTHER_OF = [
#     # According to Haojun, this is used at the beginning of the bot's utterance, when the user just gave a reason
#     # and we are agreeing with them.

#     # These templates are for reasons that begin with 'of'
#     "That's so true, you're right. Oh, that reminds me, I also think {phrase} is great because {reason}.",
#     "Oh yeah, I know what you mean. It's nice to meet another fan of {phrase}! It makes me realize that another reason to be a fan of {phrase} is because {reason}.",
#     "Yeah, I totally get that. Now I think about it, I also appreciate {phrase} because {reason}.",
# ]


# REASON_POS_ANOTHER_NO_OF = [
#     # According to Haojun, this is used at the beginning of the bot's utterance, when the user just gave a reason
#     # and we are agreeing with them.

#     # These templates are for reasons that don't begin with 'of'
#     "That's so true, you're right. There are so many things to like about {phrase}. For example, {reason}.",
#     "Oh yeah, I know what you mean. It's nice to meet another fan of {phrase} and talk about why we love it! For example, {reason}.",
#     "Yeah, I totally get that. Oh, that reminds me of another great thing about {phrase}. {reason}.",
# ]

# # Skipped this because apparently it's not used
# # REASON_POS_SWITCH = [
# #     ("Now that I think about it, I do like {phrase} because {reason}.", ['']),
# #     ("I think {phrase} is pretty good because {reason}.", ['']),
# #     ("One reason to like {phrase} is {reason}.", [''])
# # ]

# REASON_NEG_OF = [
#     # These are templates for reasons that start with "of"
#     "I suppose the main reason I'm not into {phrase} is because {reason}."
#     "In particular, I suppose the main reason I don't love {phrase} so much is because {reason}.",
#     "Now I think about it, probably I don't love {phrase} because {reason}.",
#     "You know, I think the main reason I'm not a big fan of {phrase} is because {reason}.",
# ]

# # REASON_NEG_NO_OF = [
# #     # These are possible templates for reasons that don't start with "of".
# #     # Some of these sound great with some reasons (and in fact sound better than just saying the reason stand-alone).
# #     # But the problem with these is that they don't fit all reasons that don't start with "of",
# #     # e.g. there are quite a lot of reasons that start with "i love that", and that sounds weird with most of these.
# #     # You could potentially spend time making rules for which reasons work ok with which templates, but if we don't want to spend time on that,
# #     # my suggestion is that we just say the reasons stand-alone.
# #     ("Sometimes I think that {reason}.", ['']),
# #     ("Sometimes I feel that {reason}.", ['']),
# #     ("Sometimes I find that {reason}.", ['']),
# #     ("I do sometimes find myself thinking that {reason}.", ['']),
# #     ("I'm not sure, but I do sometimes think that {reason}.", ['']),
# #     ("I might be wrong, but I do sometimes find that {reason}.", ['']),
# # ]

# REASON_NEG_ANOTHER_OF = [
#     # According to Haojun, this is used at the beginning of the bot's utterance, when the user just gave a reason
#     # and we are agreeing with them.

#     # These templates are for reasons that begin with 'of'
#     "Yep, that's a good point about {phrase}. I shouldn't complain too much, but another reason I find that I'm not a big fan of {phrase} is because {reason}.",
#     "That's so true. Sorry if I'm begin negative, but I also find that sometimes I don't love {phrase} quite so much because {reason}.",
#     "Yeah, I think you're right. It's kind of a relief to meet another person who doesn't love {phrase}! Honestly, I think I'm not into {phrase} because {reason}.",
# ]

# REASON_NEG_ANOTHER_NO_OF = [
#     # According to Haojun, this is used at the beginning of the bot's utterance, when the user just gave a reason
#     # and we are agreeing with them.

#     # These templates are for reasons that don't begin with 'of'
#     "Yep, that's a good point about {phrase}. I shouldn't complain too much, but there are quite a few things I don't love so much about {phrase}. For example, {reason}.",
#     "That's so true. Sorry if I'm being negative, but there are some other reasons why I don't love {phrase} quite so much. For example, {reason}.",
#     "Yeah, I think you're right. It's kind of a relief to meet another person who doesn't love {phrase} and be honest about why we don't love it! {reason}.",
# ]

# # Skipped this because apparently it's not used
# # REASON_NEG_SWITCH = [
# #     ("Now that I think about it, I don't like {phrase} because {reason}.", ['']),
# #     ("I think {phrase} is not that good because {reason}.", ['']),
# #     ("One reason to not like {phrase} is {reason}.", [''])
# # ]

# SOLICIT_AGREE_SAME = [
#     # Again, I think asking "Do you agree?" so much is one of our main problems right now.
#     # We ask "do you like X" and "do you agree" too much instead of just "what do you think about X" and "<bot's opinion>, what do you think?"
#     # Do we really need to make it a yes/no question? Can't we just say our opinion and say "what do you think?", then the user reacts, then we do a vague acknowledgement and move on?

#     # According to Haojun this doesn't have to be a yes/no question and can be open-ended.

#     # yes/no versions where "yes" means agree
#     "Do you ever feel that way too?",
#     "I wonder if you feel the same way too sometimes?",
#     "Do you ever think that too?",
#     "Does that make sense?",
#     "Do you know what I mean?",

#     # More open-ended versions
#     "What do you think?",
# ]


# SOLICIT_AGREE_DIFF = [
#     # According to Haojun this doesn't have to be a yes/no question and can be open-ended

#     # yes/no versions where "yes" means agree
#     "Perhaps we can agree on that?",
#     "I don't know, maybe that's just me. Do you ever feel that way too?",
#     "Um, maybe I'm the only one who thinks that. Do you ever think that too?",
#     "Uh, I hope that made sense?",

#     # More open-ended versions
#     "What do you think?",
# ]

# SOLICIT_REASON_CONT = [
#     "What about you?",
#     "How about you?",
# ]

# SOLICIT_REASON_POS = [
#     # According to Haojun, we can assume that this comes after the user said "yes" to "do you like X",
#     # and SOLICIT_REASON_POS is the only thing in the bot's utterance
#     "Great, I'd be interested to hear what you like about {phrase}?",
#     "Cool! I'd love to hear what you appreciate most about {phrase}?",
#     "Oh yeah? Maybe you could tell me what's your favorite thing about {phrase}?",
# ]

# SOLICIT_REASON_NEG = [
#     # According to Haojun, we can assume that this comes after the user said "no" to "do you like X",
#     # and SOLICIT_REASON_NEG is the only thing in the bot's utterance
#     "Oh OK. I'd be interested to hear why you're not a big fan of {phrase}?",
#     "Oh I see. So, um, I wonder why don't you like {phrase}?",
#     "Oh yeah? Maybe you could tell me why you're not so into {phrase}?",
# ]

@dataclass
class PhrasingFeatures:
    num_reasons_given_since_switch : int
    is_turn1 : bool
    sentiment_switched : bool
    prev_solicit_reason : bool
    disagree : bool
    is_prompt : bool

def add_user_like(meta_templates: List[str], action : Action, phrasing_features : PhrasingFeatures):
    if action.give_agree and phrasing_features.disagree:
        meta_templates.append('{sorry_i_dislike}')
    elif action.give_agree and phrasing_features.is_turn1:
        meta_templates.append('{i_also_like}')
    elif action.give_agree and phrasing_features.sentiment_switched:
        meta_templates.append('{you_convinced_me}')
    elif action.give_agree and phrasing_features.prev_solicit_reason and not phrasing_features.sentiment_switched:
        meta_templates.append('{i_agree_with_your_reason}')
    elif action.give_agree:
        meta_templates.append('{i_also_like}')

def add_user_dislike(meta_templates: List[str], action : Action, phrasing_features : PhrasingFeatures):
    if action.give_agree and phrasing_features.disagree:
        meta_templates.append('{sorry_i_like}')
    elif action.give_agree and phrasing_features.is_turn1:
        meta_templates.append('{i_also_dislike}')
    elif action.give_agree and phrasing_features.sentiment_switched:
        meta_templates.append('{you_convinced_me}')
    elif action.give_agree and phrasing_features.prev_solicit_reason and not phrasing_features.sentiment_switched:
        meta_templates.append('{i_agree_with_your_reason}')
    elif action.give_agree:
        meta_templates.append('{i_also_dislike}')

def add_i_like_reason(meta_templates : List[str], action : Action,
        reason : Optional[str], phrasing_features : PhrasingFeatures) -> None:
    # Tell the user a reason if we chose to
    if reason is None:
        return
    elif phrasing_features.sentiment_switched:
        if reason.startswith('of'): meta_templates.append('{now_i_like_because_of}')
        elif reason.startswith('i feel like'): meta_templates.append('{reason_no_nothing}')
        else: meta_templates.append('{reason_no_of}')
    elif phrasing_features.num_reasons_given_since_switch == 0 and not phrasing_features.sentiment_switched:
        if reason.startswith('of'): meta_templates.append('{i_like_because_of}')
        elif reason.startswith('i feel like'): meta_templates.append('{reason_no_nothing}')
        else: meta_templates.append('{reason_no_of}')
    elif (phrasing_features.num_reasons_given_since_switch > 0 and not phrasing_features.sentiment_switched):
        if reason.startswith('of'): meta_templates.append('{another_reason_i_like_is_of}')
        else: meta_templates.append('{another_reason_i_like_is}')

def add_i_dislike_reason(meta_templates : List[str], action : Action,
        reason : Optional[str], phrasing_features : PhrasingFeatures) -> None:
    # Tell the user a reason if we chose to
    if reason is None:
        return
    elif phrasing_features.sentiment_switched:
        if reason.startswith('of'): meta_templates.append('{now_i_dislike_because_of}')
        elif reason.startswith('i feel like'): meta_templates.append('{reason_no_nothing}')
        else: meta_templates.append('{reason_no_of}')
    elif phrasing_features.num_reasons_given_since_switch == 0 and not phrasing_features.sentiment_switched:
        if reason.startswith('of'): meta_templates.append('{i_dislike_because_of}')
        elif reason.startswith('i feel like'): meta_templates.append('{reason_no_nothing}')
        else: meta_templates.append('{reason_no_of}')
    elif (phrasing_features.num_reasons_given_since_switch > 0 and not phrasing_features.sentiment_switched):
        if reason.startswith('of'): meta_templates.append('{another_reason_i_dislike_is_of}')
        else: meta_templates.append('{another_reason_i_dislike_is}')

def add_user_like_solicit(meta_templates: List[str], action : Action, phrasing_features : PhrasingFeatures) -> None:
    # Ask user a question
    if action.solicit_agree:
        meta_templates.append('{do_you_agree}')
    elif action.solicit_reason and not phrasing_features.disagree:
        if not action.give_reason and not phrasing_features.is_prompt:
            meta_templates.append('{oh_why_do_you_like}')
        elif not action.give_reason and phrasing_features.is_prompt:
            meta_templates.append('{why_do_you_like}')
        else:
            meta_templates.append('{what_about_you}')
    elif action.solicit_reason and phrasing_features.disagree:
        meta_templates.append('{but_interested_to_know_why_you_like}')
    elif action.suggest_alternative:
        meta_templates.append('{hmm_do_you_like_alt_also}')

def add_user_dislike_solicit(meta_templates: List[str], action : Action, phrasing_features : PhrasingFeatures) -> None:
    # Ask user a question
    if action.solicit_agree:
        meta_templates.append('{do_you_agree}')
    elif action.solicit_reason and not phrasing_features.disagree:
        if not action.give_reason and not phrasing_features.is_prompt:
            meta_templates.append('{oh_why_do_you_dislike}')
        elif not action.give_reason and phrasing_features.is_prompt:
            meta_templates.append('{why_do_you_dislike}')
        else:
            meta_templates.append('{what_about_you}')
    elif action.solicit_reason and phrasing_features.disagree:
        meta_templates.append('{but_interested_to_know_why_you_dislike}')
    elif action.suggest_alternative:
        meta_templates.append('{hmm_do_you_like_alt_instead}')

def fancy_utterancify(state : State, action : Action, positive_reasons : List[str], negative_reasons : List[str],
        alternatives : List[str], should_evaluate : bool, choice_fn: Callable[[List[str]], str], is_prompt: bool = False, additional_features = None) -> Tuple[str, str, Optional[str]]:

    # First, select reasons and alternative if needed
    reason = None
    alternative = None
    if action.give_reason and action.sentiment > 2:
        reason = choice_fn(positive_reasons)
    elif action.give_reason and action.sentiment < 2:
        reason = choice_fn(negative_reasons)
    if action.suggest_alternative:
        alternative = random.choice(alternatives)

    # Get phrasing features
    switch_indices = [i for i in range(len(state.action_history)) if state.action_history[i].suggest_alternative \
        or state.action_history[i].solicit_opinion\
        or state.action_history[i].solicit_disambiguate]
    switch_index = switch_indices[-1] if len(switch_indices) > 0 else 0
    num_reasons_given_since_switch = sum(action.give_reason for action in state.action_history[switch_index:])
    is_turn1 = len(state.action_history) == 0
    prev_solicit_reason = not is_turn1 and state.action_history[-1].solicit_reason
    sentiment_switched = not is_turn1 and abs(state.action_history[-1].sentiment - action.sentiment) == 4 # We didn't like it before, but we like it now
    phrasing_features = PhrasingFeatures(
        num_reasons_given_since_switch,
        is_turn1, sentiment_switched,
        prev_solicit_reason,
        abs(state.cur_sentiment - action.sentiment) == 4,
        is_prompt)

    # Next, generate the template based on the action and reasons
    opinionable_phrase = state.cur_phrase
    if opinionable_phrase == '':
        raise RuntimeError('Cannot utterancify when there is no opinionable phrase')
    meta_templates = []
    if action.solicit_opinion:
        meta_templates.append('{do_you_like}')
    elif action.sentiment > 2 and state.cur_sentiment > 2: # Agreement (like, like)
        add_user_like(meta_templates, action, phrasing_features)
        add_i_like_reason(meta_templates, action, reason, phrasing_features)
        add_user_like_solicit(meta_templates, action, phrasing_features)
    elif action.sentiment < 2 and state.cur_sentiment < 2: # Agreement (dislike, dislike)
        add_user_dislike(meta_templates, action, phrasing_features)
        add_i_dislike_reason(meta_templates, action, reason, phrasing_features)
        add_user_dislike_solicit(meta_templates, action, phrasing_features)
    elif action.sentiment > 2 and state.cur_sentiment < 2: # Disagreement (like, dislike)
        add_user_dislike(meta_templates, action, phrasing_features)
        add_i_like_reason(meta_templates, action, reason, phrasing_features)
        add_user_dislike_solicit(meta_templates, action, phrasing_features)
    elif action.sentiment < 2 and state.cur_sentiment > 2: # Disagreement (dislike, like)
        add_user_like(meta_templates, action, phrasing_features)
        add_i_dislike_reason(meta_templates, action, reason, phrasing_features)
        add_user_like_solicit(meta_templates, action, phrasing_features)
    elif action.sentiment == 2 and state.cur_sentiment == 2: # We both are neutral about the entity
        pass
    elif action.sentiment > 2 and state.cur_sentiment == 2: # Disagreement (like, neutral)
        pass
    elif action.sentiment < 2 and state.cur_sentiment == 2: # Disagreement (dislike, neutral)
        pass
    elif action.sentiment == 2 and state.cur_sentiment < 2: # Conservative (neutral, dislike)
        add_user_dislike_solicit(meta_templates, action, phrasing_features)
    elif action.sentiment == 2 and state.cur_sentiment > 2: # Conservative (neutral, like)
        add_user_like_solicit(meta_templates, action, phrasing_features)
    if action.exit and additional_features is not None and additional_features.detected_no:
        meta_templates.append('{hard_exit_conversation}')
    elif action.exit and should_evaluate:
        meta_templates.append('{thanks_for_sharing_eval}')
    elif action.exit:
        meta_templates.append('{thanks_for_sharing}')

    chosen_meta_templates = [choice_fn(PHRASING_TEMPLATES[meta_template]) for meta_template in meta_templates]
    utterance_f = ' '.join([meta_template for meta_template in chosen_meta_templates if meta_template is not None])
    '''
    if '{do_you_like}' in meta_templates and len(meta_templates) == 1 and generic:
        transition = random.choice(DO_YOU_LIKE_TRANSITIONS)
        utterance_f = transition + utterance_f
    '''
    bot_utterance = utterance_f.format(phrase=opinionable_phrase, reason=reason if reason is not None else '', alternative=alternative if alternative is not None else '')
    return bot_utterance, opinionable_phrase if alternative is None else alternative, reason

def fancy_utterancify_prompt(state : State, action : Action, positive_reasons : List[str], negative_reasons : List[str], \
            alternatives : List[str], generic : bool, choice_fn : Callable[[List[str]], str]) -> Tuple[str, str, Optional[str]]:
    bot_utterance, opinionable_phrase, reason = fancy_utterancify(state, action, positive_reasons, negative_reasons, alternatives, False, choice_fn, is_prompt=True)
    meta_template = ''
    transition = ''
    if state.cur_sentiment < 2:
        meta_template = '{i_remember_you_dislike}'
    elif state.cur_sentiment == 2 and not generic:
        meta_template = '{you_mentioned}'
    elif state.cur_sentiment > 2:
        meta_template = '{i_remember_you_like}'
    utterance_f = choice_fn(PHRASING_TEMPLATES[meta_template]) if meta_template != '' else ''
    '''
    if generic:
        transition = random.choice(MENTION_REMEMBER_TRANSITIONS)
    '''
    preface = transition + utterance_f.format(phrase=opinionable_phrase)
    return ' '.join([preface, bot_utterance]), opinionable_phrase, reason
