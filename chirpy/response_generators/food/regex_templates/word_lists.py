import os
from os.path import abspath, dirname
import json

with open(os.path.join(abspath(dirname(__file__)), 'scraped_final.json')) as datafile:
    f = json.load(datafile)
    FOODS = f['foods']
    INGREDIENTS = f['ingredients']
    CATEGORIES = f['categories']

YES_WORDS = [
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
    "course",
    "duh"
]

NO_WORDS = [
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
    "awful",
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
    "hated",
    "loathed",
    "detested",
    "despised",
    "disliked",
    "abhored",
    "couldn't bear",
    "couldn't stand"
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

KEYWORD_FOODS = [
    "ice cream",
    "cheese",
    "pizza"
]

TYPES = [
    "chocolate",
    "vanilla",
    "cheddar",
    "monterey jack",
    "american",
    "pepperoni",
    "cheese",
]

WATCH_WORDS = [
    "watched",
    "viewed",
    "saw"
]

KEYWORD_TEAM = [
    "team",
    "group"
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
    "show me",
    "elaborate on",
    "expand on",
    "switch to",
    "change to",
    "can you tell me",
    "can you give me",
    "can you show me",
    "can you say",
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
    "let's chat about",
    "let's discuss",
    "can we talk about",
    "can we chat about",
    "can we discuss",
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
    "i'm curious about",
    "talk about",
    "we talk about"
]

BAD_WORDS = ['diet', 'fat', 'obese', 'exercise', 'sorry', 'disgusting', 'hate', 'dislike', 'you', 'beer', 'alcohol', 'wine', 'drunk'] # seem to pop up
