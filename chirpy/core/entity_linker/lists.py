"""
Lists of words and phrases to be used in the entity linker.

If you want to fix something in the entity linker, one of the following problems and solutions might match your situation:


- Problem 1: A span is getting linked to an entity/entities, but it shouldn't ever be linked to any entity.

    Solution: Add the unigrams to DONT_LINK_WORDS.
    Consequence: The entity linker will not attempt to link any span consisting of DONT_LINK_WORDS.

    Solution: Add the whole span to LOW_PREC_SPANS.
    Consequence: This exact span and any linked entities will only be in the low precision set, not the high precision set.

- Problem 2: A span is getting linked to an entity/entities in the high precision set, but it should be in the low
    precision set.

    Solution: Add the unigrams to ADDITIONAL_HIGH_FREQ_WORDS.
    Consequence: If a span contains only high-frequency words, as determined by our unigram frequency statistics and ADDITIONAL_HIGH_FREQ_WORDS, it and any linked entities will only ever be in the low precision set, not the high precision set.

    Solution: Add the whole span to LOW_PREC_SPANS.
    Consequence: This exact span and any linked entities will only be in the low precision set, not the high precision set.

- Problem 3: A span is not getting linked at all, but it should.
- Problem 4: A span is getting linked to the wrong entity (i.e. the top entity in the LinkedSpan is the wrong one).

    Solution: Add the span and the correct entity to MANUAL_SPAN2ENTINFO with force_high_prec=False.
    Consequence: The entity linker will always link this span and consider this entity to be the top entity, but it
        won't force it to be in the high precision set (i.e., normal rules apply).

- Problem 5: A span is getting linked to the correct top entity, but it's in the low precision set and should be in
    the high precision set.

    Solution: Add the span and the correct entity to MANUAL_SPAN2ENTINFO with force_high_prec=True.
    Consequence: The entity linker will always link this span and consider this entity to be the top entity, and it
        will force it to be in the high precision set (potentially eliminating other spans that are nested with it).


You can check that your fix is working by running the code at the bottom of entity_linker.py.
"""

import os
from chirpy.core.util import get_unigram_freq_fn, load_text_file
from chirpy.core.entity_linker.util import wiki_url_to_name
from chirpy.core.entity_linker.util import NUMBER_ALTERNATIVES

# Load stopwords
STOPWORDS_FILEPATH = os.path.join(os.path.dirname(__file__), '../../data/long_stopwords.txt')
STOPWORDS = load_text_file(STOPWORDS_FILEPATH)  # set of strings

COMMONWORDS_FILEPATH = os.path.join(os.path.dirname(__file__), '../../data/common_words.txt')
COMMONWORDS = load_text_file(STOPWORDS_FILEPATH)  # set of strings

STOPWORDS.update(COMMONWORDS)
STOPWORDS.update(set([str(x) for x in range(100)]))  # add single numbers
STOPWORDS.update({w for word_set in NUMBER_ALTERNATIVES for w in word_set if len(w.split())==1})

# DONT_LINK_WORDS primarily contains very common words like stopwords.
# If a span is a single DONT_LINK_WORDS (e.g. span="the"), we never attempt to link it at all.
# If a span has more than one word, all of which are DONT_LINK_WORDS, we won't attempt to link it at all, unless
# there's an expected_type, in which case it will be considered.
DONT_LINK_WORDS = {w for w in STOPWORDS}
DONT_LINK_WORDS.update(set(['alexa', 'question', 'subject', 'conversation', 'talk', 'chat', 'watched', 'watching',
                            'ok', 'well', 'bot', 'bots', 'chatbot', 'socialbot', 'social', 'lot', 'play', 'played', 'playing',
                            'robot', 'hmm', 'book', 'ate', 'forget', 'yummy', 'goodbye', 'cancel', 'rating', 'eating',
                            'lol', 'nevermind', 'choose', 'people', 'actor', 'actors', 'belief', 'beliefs', 'ai',
                            'subject', 'love', 'tone', 'song', 'sound', 'live', 'book', 'reading', 'flavor', 'scouts',
                            'tomorrow', 'today', 'yesterday', 'truth', 'false', 'dream', 'yes', 'no', 'color',
                            'mom', 'dad', 'mommy', 'daddy', 'sister', 'brother', 'aunt', 'uncle', 'parent', 'house',
                            'idiot', 'drink', 'echo', 'film', 'over', 'hello', 'skip']))
assert all([len(span.split()) == 1 for span in DONT_LINK_WORDS]), 'Only put unigrams in DONT_LINK_WORDS'

# Load spoken unigram frequencies from chirpy/data/2_2_spokenvwritten.txt
# Everything above a threshold is treated as a high frequency unigram.
get_unigram_freq_orig = get_unigram_freq_fn()  # this fn maps a unigram str to an int

# Manually add some additional high freq unigrams.
# We use unigram frequency as a filter to decide whether a LinkedSpan goes in the high precision or low precision set.
# If a LinkedSpan's span contains only high frequency unigrams, it goes in the low precision set.
ADDITIONAL_HIGH_FREQ_WORDS = {w for w in DONT_LINK_WORDS}  # all DONT_LINK_WORDS are considered high frequency
ADDITIONAL_HIGH_FREQ_WORDS.update(set(['mom']))  # you can add more here
assert all([len(span.split()) == 1 for span in ADDITIONAL_HIGH_FREQ_WORDS]), 'Only put unigrams in ADDITIONAL_HIGH_FREQ_WORDS. Put multi-word phrases in LOW_PREC_SPANS'

def get_unigram_freq(unigram: str) -> int:
    """
    Returns the frequency of a unigram.
    If the unigram is in ADDITIONAL_HIGH_FREQ_WORDS, returns inf.
    If the unigram is in our list of common spoken unigrams and their frequencies, return that frequency.
    Otherwise, return 0.
    """
    if unigram in ADDITIONAL_HIGH_FREQ_WORDS:
        return float('inf')
    return get_unigram_freq_orig(unigram)

# If a span is in LOW_PREC_SPANS, we always put it in the low_prec set
# This list was initialized with the ngrams from chirpy/data/2_2_spokenvwritten.txt
LOW_PREC_SPANS = set(
  ['a bit', 'a little', 'a little bit', 'a lot', 'according to', 'ahead of', 'all of a sudden', 'all right',
   'all the same', 'along with', 'and so forth', 'and so on', 'apart from', 'as if', 'as it were', 'as long as',
   'as opposed to', 'as soon as', 'as though', 'as to', 'as well', 'as well as', 'at all', 'at first', 'at last',
   'at least', 'at present', 'away from', 'because of', 'brand new', 'by now', 'co op', 'depending on', 'due to',
   'each other', 'even if', 'even though', 'even when', 'ever so', 'except for', 'fed up', 'for example',
   'for instance', 'given that', 'half way', 'in addition to', 'in between', 'in case', 'in charge of', 'in favour of',
   'in front of', 'in general', 'in order', 'in particular', 'in relation to', 'in terms of', 'in touch with',
   'instead of', 'just about', 'kind of', 'less than', 'more than', 'next to', 'no doubt', 'no longer', 'no one',
   'now that', 'of course', 'off of', 'on behalf of', 'on board', 'on to', 'on top of', 'once again',
   'one another', 'other than', 'out of', 'outside of', 'over here', 'over there', 'per cent', 'prior to',
   'rather than', 'so that', 'sort of', 'straight away', 'subject to', 'such as', 'that is', 'up to',
   'up to date', 'whether or not', 'with regard to', 'read', 'celebrity', 'kid', 'idea', 'big fan',
   'bad', 'nice', 'cook', 'cooking',
   'red', 'blue', 'green', 'yellow', 'orange', 'black', 'purple', 'chartreuse', 'white', 'gray', 'pink' # colors
   ])          # Michael Jackson
LOW_PREC_FILEPATH = os.path.join(os.path.dirname(__file__), 'low_prec.txt')
SHORT_KEYS_FILEPATH = os.path.join(os.path.dirname(__file__), 'short_keys.txt')
LOW_PREC_SPANS |= load_text_file(LOW_PREC_FILEPATH)
LOW_PREC_SPANS |= load_text_file(SHORT_KEYS_FILEPATH)

class ManualLink(object):
    """Represents a manually-linked entity and how to handle it"""
    def __init__(self, url: str, force_high_prec: bool = False, delete_alternative_entities: bool = False):
        self.url = url
        self.ent_name = wiki_url_to_name(url)
        self.force_high_prec = force_high_prec
        self.delete_alternative_entities = delete_alternative_entities


# span -> wikipedia url mappings. Whenever we see this span, we will always:
# (a) make sure that we attempt to link this span,
# (b) make sure that this entity is among the candidates for this span,
# (c) consider this entity to be the top entity for this span, regardless of score,
# (d) if force_high_prec=True, ensure this linked span gets into the high precision set (meaning it will eliminate other spans that are nested with it)
# (e) if delete_alternative_entities=True, other possible entities for this exact span will be deleted. The candidate entities for spans nested with this span won't be affected.
# For (b) to work, the wikipedia url needs to be present in the wikipedia dump we're currently using.
MANUAL_SPAN2ENTINFO = {
    'animals': ManualLink('https://en.wikipedia.org/wiki/Animal', delete_alternative_entities=True),
    'animal': ManualLink('https://en.wikipedia.org/wiki/Animal', delete_alternative_entities=True),
    'movies': ManualLink('https://en.wikipedia.org/wiki/Film', delete_alternative_entities=True),
    'movie': ManualLink('https://en.wikipedia.org/wiki/Film', delete_alternative_entities=True),

    'fortnite': ManualLink('https://en.wikipedia.org/wiki/Fortnite_Battle_Royale', delete_alternative_entities=True),

    # for NEWS RG
    'technology': ManualLink('https://en.wikipedia.org/wiki/Technology', delete_alternative_entities=True),
    'entertainment': ManualLink('https://en.wikipedia.org/wiki/Entertainment', delete_alternative_entities=True, force_high_prec=True),
    'health': ManualLink('https://en.wikipedia.org/wiki/Health', delete_alternative_entities=True, force_high_prec=True),
    'business': ManualLink('https://en.wikipedia.org/wiki/Business', delete_alternative_entities=True, force_high_prec=True),
    'science': ManualLink('https://en.wikipedia.org/wiki/Science', delete_alternative_entities=True, force_high_prec=True),
    'sports': ManualLink('https://en.wikipedia.org/wiki/Sport', delete_alternative_entities=True),
    'sport': ManualLink('https://en.wikipedia.org/wiki/Sport', delete_alternative_entities=True),
    'book': ManualLink('https://en.wikipedia.org/wiki/Book', delete_alternative_entities=True),
    'books': ManualLink('https://en.wikipedia.org/wiki/Book', delete_alternative_entities=True),
    'school': ManualLink('https://en.wikipedia.org/wiki/School', delete_alternative_entities=True),
    'tv': ManualLink('https://en.wikipedia.org/wiki/Television', delete_alternative_entities=True),
    'tv show': ManualLink('https://en.wikipedia.org/wiki/Television', delete_alternative_entities=True),
    'country music': ManualLink('https://en.wikipedia.org/wiki/Country_music', delete_alternative_entities=True),
    'cats': ManualLink('https://en.wikipedia.org/wiki/Cat'),  # don't want to delete Cats the musical/movie
    'cars': ManualLink('https://en.wikipedia.org/wiki/Car'),  # don't want to delete Cars the movie
    'songs': ManualLink('https://en.wikipedia.org/wiki/Song', delete_alternative_entities=True),
    'song': ManualLink('https://en.wikipedia.org/wiki/Song', delete_alternative_entities=True),
    'celebrity': ManualLink('https://en.wikipedia.org/wiki/Celebrity', delete_alternative_entities=True),
    'celebrities': ManualLink('https://en.wikipedia.org/wiki/Celebrity', delete_alternative_entities=True),
    'read': ManualLink('https://en.wikipedia.org/wiki/Reading', delete_alternative_entities=True),
    'sandwiches': ManualLink('https://en.wikipedia.org/wiki/Sandwich', delete_alternative_entities=True),
    'sandwich': ManualLink('https://en.wikipedia.org/wiki/Sandwich', delete_alternative_entities=True),
    'skits': ManualLink('https://en.wikipedia.org/wiki/Skit', delete_alternative_entities=True),
    'chicken nugget': ManualLink('https://en.wikipedia.org/wiki/Chicken_nugget', delete_alternative_entities=True),
    'chicken nuggets': ManualLink('https://en.wikipedia.org/wiki/Chicken_nugget', delete_alternative_entities=True),
    'san francisco': ManualLink('https://en.wikipedia.org/wiki/San_Francisco', delete_alternative_entities=True),
    'san jose': ManualLink('https://en.wikipedia.org/wiki/San_Jose,_California', delete_alternative_entities=True),

    'ahmaud arbery': ManualLink('https://en.wikipedia.org/wiki/Shooting_of_Ahmaud_Arbery', force_high_prec=True, delete_alternative_entities=True),
    'breonna taylor': ManualLink('https://en.wikipedia.org/wiki/Institutional_racism', force_high_prec=True, delete_alternative_entities=True),
    'george floyd': ManualLink('https://en.wikipedia.org/wiki/Black_Lives_Matter', force_high_prec=True, delete_alternative_entities=True),
    'black lives matter': ManualLink('https://en.wikipedia.org/wiki/Black_Lives_Matter', force_high_prec=True, delete_alternative_entities=True),
    'timothee chalamet': ManualLink('https://en.wikipedia.org/wiki/Timothée_Chalamet', force_high_prec=True, delete_alternative_entities=True),
    'mike wazowski': ManualLink('https://en.wikipedia.org/wiki/Monsters,_Inc.', force_high_prec=True, delete_alternative_entities=True),
    'the lord of the rings the fellowship of the ring': ManualLink('https://en.wikipedia.org/wiki/The_Lord_of_the_Rings:_The_Fellowship_of_the_Ring', force_high_prec=True),
    'nfl 18': ManualLink('https://en.wikipedia.org/wiki/Madden_NFL_18', force_high_prec=True),
    'animal crossing': ManualLink('https://en.wikipedia.org/wiki/Animal_Crossing:_New_Horizons', force_high_prec=True),
    'apex': ManualLink('https://en.wikipedia.org/wiki/Apex_Legends'),
    'ark survival evolved': ManualLink('https://en.wikipedia.org/wiki/Ark:_Survival_Evolved', force_high_prec=True, delete_alternative_entities=True),
    'nba2k 20': ManualLink('https://en.wikipedia.org/wiki/NBA_2K20', force_high_prec=True),
    'world war 2': ManualLink('https://en.wikipedia.org/wiki/World_War_II', force_high_prec=True, delete_alternative_entities=True),
    'world war two': ManualLink('https://en.wikipedia.org/wiki/World_War_II', force_high_prec=True, delete_alternative_entities=True),
    'world war ii': ManualLink('https://en.wikipedia.org/wiki/World_War_II', force_high_prec=True, delete_alternative_entities=True),
    'world war 1': ManualLink('https://en.wikipedia.org/wiki/World_War_I', force_high_prec=True, delete_alternative_entities=True),
    'world war one': ManualLink('https://en.wikipedia.org/wiki/World_War_I', force_high_prec=True, delete_alternative_entities=True),
    'world war i': ManualLink('https://en.wikipedia.org/wiki/World_War_I', force_high_prec=True, delete_alternative_entities=True),
    'mac and cheese': ManualLink('https://en.wikipedia.org/wiki/Macaroni_and_cheese', force_high_prec=True, delete_alternative_entities=True),
    'taylor swift': ManualLink('https://en.wikipedia.org/wiki/Taylor_Swift', force_high_prec=True, delete_alternative_entities=True),
    'darwins game': ManualLink('https://en.wikipedia.org/wiki/Darwin\'s_Game', force_high_prec=True),
    'sam and cat': ManualLink('https://en.wikipedia.org/wiki/Sam_&_Cat', force_high_prec=True),  # problem is with the ampersand. proper solution would be to convert ampersand to "and" in the ES index anchortexts
    'austin and ally': ManualLink('https://en.wikipedia.org/wiki/Austin_&_Ally', force_high_prec=True),  # problem is with the ampersand. proper solution would be to convert ampersand to "and" in the ES index anchortexts
    "magic for humans": ManualLink('https://en.wikipedia.org/wiki/Magic_for_Humans', force_high_prec=True),
    'cookies': ManualLink('https://en.wikipedia.org/wiki/Cookie', force_high_prec=True),
    'pets': ManualLink('https://en.wikipedia.org/wiki/Pet', force_high_prec=True),
    'tiger': ManualLink('https://en.wikipedia.org/wiki/Tiger', force_high_prec=True),
    'gummy': ManualLink('https://en.wikipedia.org/wiki/Gummy_candy', force_high_prec=True, delete_alternative_entities=True),
    'tigers': ManualLink('https://en.wikipedia.org/wiki/Tiger', force_high_prec=True),
    'john adams': ManualLink('https://en.wikipedia.org/wiki/John_Adams', force_high_prec=True),
    'wings of fire': ManualLink('https://en.wikipedia.org/wiki/Wings_of_Fire_(novel_series)', force_high_prec=True, delete_alternative_entities=True),
    'horse': ManualLink('https://en.wikipedia.org/wiki/Horse', force_high_prec=True, delete_alternative_entities=True),
    'horses': ManualLink('https://en.wikipedia.org/wiki/Horse', force_high_prec=True, delete_alternative_entities=True),
    'victorious': ManualLink('https://en.wikipedia.org/wiki/Victorious', force_high_prec=False),
    'chocolate chips': ManualLink('https://en.wikipedia.org/wiki/Chocolate_chip', force_high_prec=False, delete_alternative_entities=True),
    'chocolate chip': ManualLink('https://en.wikipedia.org/wiki/Chocolate_chip', force_high_prec=False, delete_alternative_entities=True),
    'penguin': ManualLink('https://en.wikipedia.org/wiki/Penguin', force_high_prec=True, delete_alternative_entities=True),
    'penguins': ManualLink('https://en.wikipedia.org/wiki/Penguin', force_high_prec=True, delete_alternative_entities=True),
    'potatoes': ManualLink('https://en.wikipedia.org/wiki/Potato', force_high_prec=True, delete_alternative_entities=True),
    'potato': ManualLink('https://en.wikipedia.org/wiki/Potato', force_high_prec=True, delete_alternative_entities=True),

    # Entity Linker
    'alaska': ManualLink('https://en.wikipedia.org/wiki/Alaska'),
    'chess': ManualLink('https://en.wikipedia.org/wiki/Chess'),
    'joe biden': ManualLink('https://en.wikipedia.org/wiki/Joe_Biden'),
    'brownies': ManualLink('https://en.wikipedia.org/wiki/Chocolate_brownie', force_high_prec=True, delete_alternative_entities=True)
}

MANUAL_TALKABLE_NAMES = {
    'hamburger': 'hamburgers',
    'chocolate brownie': 'brownies',
    'apple': 'apples'
}


# Whitelist for Wikidata categories that trigger the offensive classifier (which means the entity gets discarded),
# but we don't want to generally whitelist the phrase in the offensive classifier itself.
WIKIDATA_CATEGORY_WHITELIST = ['slave holder']

# Whitelist for Wikipedia articles that we do want to be able to discuss, but they trigger the offensive classifier
# (because the title or one of the wikidata categories is classified as offensive).
# If the problem is better solved by removing from blacklist, or whitelisting the offending phrase in
# offensive_classifier.py, do that, but if we don't want to generally whitelist that phrase, add the entity title here.
ENTITY_WHITELIST = ['George Washington', 'Cardi B']
