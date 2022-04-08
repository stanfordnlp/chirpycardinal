from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT_POST, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID

# https://www.thefreedictionary.com/List-of-pronouns.htm
FIRST_PERSON_WORDS_I = [
    "i", "i'd", "i've", "i'll", "i'm"
]

FIRST_PERSON_WORDS_ME = [
    "me", "my", "myself", "mine"
]

THIRD_PERSON_WORDS = [
    "she", "he", "it"
]
AFFLICTION = ["died", "afflication", "passed away", "die", "dying", "cancer", "bullied"]

NEGATIVE_EMOTION_WORDS = ['angry', 'annoyed', 'anxious', 'ashamed', 'awful', 'awkward', 'bitter',
                          'challenging', 'cried', 'cry', 'depressed', 'depressing', 'desperate',
                          'disappointed', 'disappointing', 'disgusted', 'frustrated', 'frustrating',
                          'hopeless', 'horrible', 'hurt',
                          'irritated', 'miserable', 'nervous', 'overwhelmed', 'painful', 'pissed', 'sad',
                          'saddening', 'stressful', 'terrible', 'tired', 'tough', 'unbearable', 'uncomfortable',
                          'unhappy', 'unpleasant', 'upset', 'upsetting', 'worried', 'grieving', 'grief',   #'hate', 'hated', 'hating',
                          'lonely', 'isolated']

class PersonalSharingTemplate(RegexTemplate):
    slots = {
        'i': FIRST_PERSON_WORDS_I,
        "my": FIRST_PERSON_WORDS_ME,
        'affliction': AFFLICTION,
        'negative_word': NEGATIVE_EMOTION_WORDS
    }
    templates = [
        # OPTIONAL_TEXT_PRE + "{pronoun_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{i}" + OPTIONAL_TEXT_MID + "{affliction}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{my}" + OPTIONAL_TEXT_MID + "{affliction}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{i}" + OPTIONAL_TEXT_MID + "{negative_word}" + OPTIONAL_TEXT_POST
         ]
    positive_examples = [
        ("my dog died recently", {"my": 'my', "affliction": "died"}),
        ('my aunt passed away', {'my': 'my', 'affliction': 'passed away'}),
        ("i'm so lonely", {'i': "i'm", "negative_word": "lonely"}),
        ("i am miserable", {'i': 'i', 'negative_word': 'miserable'}),
        ("well i get bullied a lot", {'i': 'i', 'affliction': 'bullied'})
    ]
    negative_examples = [
        "No, there isn't a problem",
        'Did you want to talk about something?',
        "george washington died very suddenly",
        "retired",
        "my name is corinne lonely faulkner"
    ]

class PersonalSharingContinuedTemplate(PersonalSharingTemplate):
    slots = PersonalSharingTemplate.slots
    slots['third_person_word'] = THIRD_PERSON_WORDS

    templates = PersonalSharingTemplate.templates + [
        OPTIONAL_TEXT_PRE + "{third_person_word}" + OPTIONAL_TEXT_MID + "{affliction}" + OPTIONAL_TEXT_POST
    ]

    positive_examples = PersonalSharingTemplate.positive_examples + [
        ("she died very suddenly", {"third_person_word": "she", "affliction": "died"})
    ]