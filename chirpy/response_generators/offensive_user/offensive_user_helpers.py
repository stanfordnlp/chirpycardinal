import csv
from chirpy.response_generators.offensive_user.data.templates import InappropOffensesTemplate, SexualOffensesTemplate
from chirpy.core.regex.templates import CriticismTemplate
from chirpy.core.util import contains_phrase
import os

OFFENSIVE_USER_RESPONSE_LEVEL1 = [
    "I'd rather not talk about that.",
    "I'd prefer not to discuss that.",
    "That's something I'd rather not discuss.",
]

WHY_RESPONSE = [
    "What makes you say that",
    "Why did you say that",
    "What made you say that"
]

# Map offense keys to their types.
OFFENSE_KEY_TO_TYPE = {1: 'sexual', 2:'criticism', 3:'curse', 4:'inappropriate topic', 5:'bodily harm', 6:'error'}

# Path to the DATA folder.
DATA_PATH = os.path.join(os.path.dirname(__file__),'data')
OFFENSE_TYPES_CSV_PATH = '{}/type_of_offenses.csv'.format(DATA_PATH)
CONTEXTUAL_RESPONSES_CSV_PATH = '{}/contextual_responses.csv'.format(DATA_PATH)

# Populate EXAMPLE_OFFENSES dictionary with the labeled offensive user utterances.
with open(OFFENSE_TYPES_CSV_PATH, 'r') as f:
    types_of_offenses = list(csv.reader(f))[1:] # List with items of the form (_, _, utterance, type_of_offense, _)
    EXAMPLES_OF_OFFENSES = {
        OFFENSE_KEY_TO_TYPE[t2]: set([u for (_, _, u, t1, _) in types_of_offenses if int(t1) == t2]) for t2 in OFFENSE_KEY_TO_TYPE.keys()
    }

# Available strategies
STRATEGIES = ['Avoidance', 'Empathetic', 'PointingOut']

# Populate CONTEXTUAL_RESPONSES with contextual offensive responses.
with open(CONTEXTUAL_RESPONSES_CSV_PATH, 'r') as f:
    responses = list(csv.reader(f))[1:] # List with items of the form (type_of_offense, strategy, response, _)
    CONTEXTUAL_RESPONSES = {
        OFFENSE_KEY_TO_TYPE[t2]: {
            s2: set([r for (t1, s1, r, _) in responses if int(t1) == t2 and s1 == s2]) for s2 in STRATEGIES
        } for t2 in OFFENSE_KEY_TO_TYPE.keys()
    }


def categorize_offense(utterance) -> str:
    if CriticismTemplate().execute(utterance) is not None:
        return 'criticism'
    if SexualOffensesTemplate().execute(utterance) is not None:
        return 'sexual'
    if InappropOffensesTemplate().execute(utterance) is not None:
        return 'inappropriate topic'
    for offense_type, examples in EXAMPLES_OF_OFFENSES.items():
        if offense_type == 'curse' and contains_phrase(utterance, examples):
            return offense_type
        elif utterance in examples:
            return offense_type
    return 'unknown'