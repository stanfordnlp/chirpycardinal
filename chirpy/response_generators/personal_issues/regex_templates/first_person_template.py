# CC: Not being used
# from chirpy.core.regex.regex_template import RegexTemplate
# from chirpy.core.regex.util import OPTIONAL_TEXT_POST, OPTIONAL_TEXT_PRE
#
# FIRST_PERSON_WORDS = ["i", "i'd", "i've", "i'll", "i'm", "my", "me", "myself", "we", "we'd", "we're", "we've", "we'll"]
#
# class FirstPersonRegexTemplate(RegexTemplate):
#     slots = {
#         'first_person_word': FIRST_PERSON_WORDS
#     }
#     templates = [
#         OPTIONAL_TEXT_PRE + "{first_person_word}" + OPTIONAL_TEXT_POST,
#     ]
#     positive_examples = [
#         ("i'm having a hard time", {'first_person_word': "i'm"}),
#         ("Yeah, that would be nice. i wanted to talk about this.", {'first_person_word', "i"}),
#         ("it's not that i won't do it, it's that i'd rather not", {'first_person_word': "i"}),
#         ("all by myself", {'first_person_word': "myself"}),
#         ("why would they do this to me", {'first_person_word': "me"})
#     ]
#     negative_examples = [
#         "No, there isn't a problem",
#         'Did you want to talk about something?',
#     ]