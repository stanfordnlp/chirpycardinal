from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT_POST, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID

NEGATIVE_EMOTION_WORDS = ['angry', 'annoyed', 'anxious', 'ashamed', 'awful', 'awkward', 'bitter',
                          'challenging', 'cried', 'cry', 'depressed', 'depressing', 'desperate',
                          'difficult', 'disappointed', 'disappointing', 'disgusted', 'frustrated', 'frustrating',
                          'hopeless', 'horrible', 'hurt',
                          'irritated', 'miserable', 'nervous', 'overwhelmed', 'painful', 'pissed', 'sad',
                          'saddening', 'stressful', 'terrible', 'tired', 'tough', 'unbearable', 'uncomfortable',
                          'unhappy', 'unpleasant', 'upset', 'upsetting', 'worried',                       #'hate', 'hated', 'hating',
                          'lonely', 'isolated']

POSITIVE_EMOTION_WORDS = ["happy", "joyful", "calm", "impressed", "pleased", "elated", "good", "great", "awesome"]
NEGATING_WORDS = ["not", "doesn't", "isn't", "don't", "won't", "wouldn't", "can't", "shouldn't",
                  "couldn't", "wasn't", "didn't", "shan't", "ain't", "aren't"]

class NegativeEmotionRegexTemplate(RegexTemplate):
    slots = {
        'negative_emotion': NEGATIVE_EMOTION_WORDS,
        'positive_emotion': POSITIVE_EMOTION_WORDS,
        'negator': NEGATING_WORDS
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{negative_emotion}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{negator}" + OPTIONAL_TEXT_MID + "{positive_emotion}" + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ("i'm feeling pretty sad", {'negative_emotion': "sad"}),
        ("all of this doesn't make me very happy", {'positive_emotion': "happy", 'negator': "doesn't"}),
        ("it's lonely", {'negative_emotion': 'lonely'})
    ]
    negative_examples = [
        "i'm pretty happy about how this turned out",
        'did you want to talk about something?',
    ]