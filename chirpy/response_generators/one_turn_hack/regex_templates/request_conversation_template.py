# from chirpy.core.regex.regex_template import RegexTemplate
# from chirpy.core.regex.util import OPTIONAL_TEXT, NONEMPTY_TEXT, \
#     OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST, OPTIONAL_TEXT_MID
# from chirpy.response_generators.sports.sports_utils import SPORTS
#
# class RequestConversationTemplate(RegexTemplate):
#     slots = {
#         "begin": ["alexa", "can you", "could you", "can we", "could we", "please", "let's", "wanna", "want to"],
#         "subject": ["we", "i", ]
#         "request": ["have a conversation", "talk", "talk with me", "talk to me", "chat with me", "chat to me"]
#     }
#     templates = [
#         OPTIONAL_TEXT_PRE + "{begin} {request}"
#     ]
#     positive_examples = [
#         ("i wanna have a conversation", {'begin': 'wanna', 'request': 'have a conversation'}),
#         ("i want to have a conversation", {'begin': 'want to', "request": "have a conversation"}),
#         ("alexa play baby", {"request": "alexa"}),
#         ("can you play you belong with me", {"request": "can you"}),
#         ("can we play mad libs", {"request": "can we"}),
#         ("play bon jovi", {}),
#         ("let's play a game", {"request": "let's"})
#     ]
#     negative_examples = [
#         "can we talk about food",
#         "i want to talk about movies",
#         "can we have a conversation about music"
#     ]
#
# class NotRequestPlayTemplate(RegexTemplate):
#     slots = {
#         'activity': SPORTS + ["video game", "games"]
#     }
#     templates = [
#         "play" + OPTIONAL_TEXT_MID + "{activity}",
#         "play with" + OPTIONAL_TEXT_POST,
#         OPTIONAL_TEXT_PRE + "play a lot" + OPTIONAL_TEXT_POST
#     ]
#     positive_examples = [
#         ("play basketball", {'activity': 'basketball'}),
#         ('play video games', {'activity': 'games'}),
#         ('play with my friends', {}),
#         ("play a lot of xbox", {})
#     ]
#     negative_examples = [
#     ]