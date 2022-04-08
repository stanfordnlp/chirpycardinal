ANIMATE_ENTITY_GROUPS = [
    'musician',
    'artist',
    'fashion_designer',
    'politician',
    'comedian',
    'actor'
]

MASC_PRONOUNS = ['he', 'him', 'his']
FEM_PRONOUNS = ['she', 'her']


def guess_pronoun(sentences):
    pronouns = {'m': 0, 'f': 0}
    for sentence in sentences:
        for word in sentence.split():
            word = word.lower()
            if word in MASC_PRONOUNS: pronouns['m'] += 1
            elif word in FEM_PRONOUNS: pronouns['f'] += 1
    key = max(pronouns, key=lambda p: pronouns[p])
    key_to_pronoun = {
        'm': ('he', 'him', 'his'),
        'f': ('she', 'her', 'her')
    }
    return key_to_pronoun[key]


def is_animate(ent_group):
    return ent_group in ANIMATE_ENTITY_GROUPS


def get_pronoun(ent_group, sentences):
    if is_animate(ent_group):
        return guess_pronoun(sentences)
    else:
        return 'it', 'it', 'its'
