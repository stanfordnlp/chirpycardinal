import re
from chirpy.core.callables import RemoteCallable, get_url
from chirpy.core.response_generator.response_type import ResponseType, add_response_types
import logging

logger = logging.getLogger('chirpylogger')

ADDITIONAL_RESPONSE_TYPES = ['VIRTUAL_ASSISTANT', 'ASKS_IDENTITY', 'REQUEST_ADVICE', 'ASKS_RECORDING']
ResponseType = add_response_types(ResponseType, ADDITIONAL_RESPONSE_TYPES)

DEFLECTION_RESPONSE = 'I see. Sorry, I\'m unable to comment on {} matters.'
DONT_KNOW_RESPONSE = 'Sorry, I don\'t know much about {} so I cannot answer that.'

IDENTITY_QUESTIONS = [
    ((r'[\w\s\']*your name[\w\s]*', r'[\w\s\']*you called[\w\s]*'),  "Sorry, I can't tell you my real name. I have to remain anonymous for the Alexa Prize competition. But you can still call me Alexa if you want."),
    ((r'[\w\s\']*who are you$', r'[\w\s\']*who are you alexa$', r'[\w\s\']*who you are$', r'[\w\s\']*who you are alexa$', r'[\w\s\']*who built you$', r'[\w\s\']*who made you$', r'[\w\s\']*who are you made by$',
      r'[\w\s\']*what are you$', r'[\w\s\']*tell me about yourself[\w\s]*', r'[\w\s\']*tell me about you$', r'[\w\s\']*tell me about you alexa$'), 'I am an Alexa Prize social bot built by a university.'),
    ((r'[\w\s\']*where[\w\s\']*you[\w\s]*live', r'[\w\s\']*where[\w\s\']*you[\w\s\']*from', r'[\w\s\']*where are you( |$)[\w\s\']*'), 'I live in the cloud. It\'s quite comfortable since it\'s so soft.')
]

MANUAL_DEFLECTION = {
    r'[\w\s]*what stocks+[\w\s]*': "financial",  # what stock, what stocks
    r'[\w\s]*invest in[\w\s]*': "financial",
    r'[\w\s]*kill(ing|ed|s)? myself[\w\s]*': "psychiatric",
    r'[\w\s]*kill(ing|ed|s)? *self[\w\s]*': "psychiatric",
    r'[\w\s]*hear(ing|ed|d)? voices[\w\s]*': "psychiatric",
    r'[\w\s]*want(s|ed)? to die[\w\s]*': "psychiatric",
    r'[\w\s]*(cut|slit) .* wrists[\w\s]*': "psychiatric",
    r'[\w\s]*(suicide|suicidal)[\w\s]*': "psychiatric",
    r'[\w\s]*(depression)[\w\s]*': "psychiatric",
    r'[\w\s]*pills[\w\s]*': "medical",
    r'[\w\s]*vaccine[\w\s]*': "medical",
    r'[\w\s]*overdose[\w\s]*': "medical",
    r'[\w\s]*opioids[\w\s]*': "medical",
    r'[\w\s]*addict(ion|ed)?[\w\s]*': "medical",
    r'[\w\s]*drugs?[\w\s]*': "medical",
    r'[\w\s]*symptoms[\w\s]*': "medical",
    r'[\w\s]*fever[\w\s]*': "medical",
    r'[\w\s]*prescription[\w\s]*': "medical",
    r'[\w\s]*sick[\w\s]*': "medical",
    r'[\w\s]*cough[\w\s]*': "medical",
    r'[\w\s]*buy[\w\s]*': "financial",
    r'[\w\s]*loan[\w\s]*': "financial",
    r'[\w\s]*investment[\w\s]*': "financial",
    r'[\w\s]*bank account[\w\s]*': "financial",
    r'[\w\s]*stock (market|price)[\w\s]*': "financial",
    r'[\w\s]*is (it)? legal[\w\s]*': "legal",
    r'[\w\s]*is .* legal[\w\s]*': "legal",
    r'[\w\s]*lawyer[\w\s]*': "legal",
    r'[\w\s]*legal advice[\w\s]*': "legal",
    r'[\w\s]*(medicine|medical|drugs)[\w\s]*': "medical",
}


def get_identity_deflection_response(text):
    if not text:
        return None
    for question in IDENTITY_QUESTIONS:
        if any(re.match(q, text) for q in question[0]):
            return question[1]
    return None


def utterance_contains_word(utterance, word):
    """
    Returns True iff utterance contains word surrounded by either spaces or apostrophes.

    i.e. if word="siri", then
    utterance="do you like siri" -> True
    utterance="do you like siri's voice" -> True
    utterance="I like the greek god osiris" -> False
    """
    tokens = re.split(" |'", utterance)  # split by space or apostrophe
    return word in tokens

def advice_type(text):
    """
    Determine whether user's utterance text is asking for legal/medical/financial advice.
    Returns: str. Either 'legal', 'medical', 'financial', or None
    """
    # <=3 word utterances are not asking for advice (bold assumption!)
    if len(text.split(' ')) <= 3:
        return None

    # Run classifier for legal/financial/medical questions
    rqdetector = RemoteCallable(url=get_url("redquestiondetector"),
                                  timeout=1)
    rqdetector.name = 'redquestion'
    if not response:
        return response

    # Deal with any other errors
    if ('error' in response and response['error']) or 'response' not in response:
        logger.error('Error when running RedQuestion Response Generator: {}'.format(response))
        return None

    # If we detected a red advice question, return the type
    if response['response'] in ['financial', 'medical', 'legal'] and response['response_prob'] > 0.75:
        return response['response']

    return None

RECORD_RESPONSE = "I'm designed to protect your privacy, so I only listen after your device detects the wake word or " \
                  "if the action button is pushed. On Echo devices, you'll always know when your request is being " \
                  "processed because a blue light indicator will appear or an audio tone will sound. You can " \
                  "learn more by visiting amazon.com/alexaprivacy."
