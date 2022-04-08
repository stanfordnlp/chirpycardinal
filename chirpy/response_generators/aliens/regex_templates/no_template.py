# CC: Not being used for now.
# from chirpy.core.regex.regex_template import RegexTemplate
# from chirpy.core.regex.util import OPTIONAL_TEXT, OPTIONAL_TEXT_POST, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID
#
# NO_WORDS = [
#     "no",
#     "don't",
#     'neither',
#     "i don't know",
#     'else',
#     'nothing',
#     'nope',
#     "haven't",
#     "absolutely not",
#     "most certainly not",
#     "of course not",
#     "under no circumstances",
#     "by no means",
#     "not at all",
#     "negative",
#     "never",
#     "not really",
#     "nope",
#     "uh-uh",
#     "nah",
#     "not on your life",
#     "no way",
#     "no way Jose",
#     "ixnay",
#     "nay",
#     "not"]
#
# class NoTemplate(RegexTemplate):
#     slots = {
#         'no_word': NO_WORDS,
#     }
#     templates = [
#         OPTIONAL_TEXT_PRE + "{no_word}" + OPTIONAL_TEXT_POST
#     ]
#     positive_examples = [
#         "no",
#         "no i don't want to talk about that",
#         "please don't talk about that",
#         "don't talk about that anymore",
#         "i do not want to hear more"
#     ]
#     negative_examples = [
#         "ok",
#         "sure",
#         "ok please tell me more",
#         "i would really like to hear more"
#
#     ]