import random

from chirpy.core.response_generator import nlg_helper

ACKNOWLEDGMENTS = [
    "That's an interesting point.",
    "That sounds reasonable to me.",
    "I hadn't thought about it that way.",
    "That's an interesting thought.",
    "That's an interesting way of putting it."
]

@nlg_helper
def get_ack():
	return random.choice(ACKNOWLEDGMENTS)