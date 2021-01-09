import logging
import os
import string
from chirpy.core.util import load_text_file, contains_phrase

logger = logging.getLogger('chirpylogger')

SPECIAL_CHARS = "!\"#$%&()+,./:;<=>?[\\]^_`{|}~"

# Offensive phrases which are in offensive_phrases_preprocessed.txt, that you want to remove
# Enter them exactly as they appear in offensive_phrases_preprocessed.txt
REMOVE_FROM_BLACKLIST = set(['god', 'gods', 'ginger', 'gay', 'lesbian', 'lesbians', 'balls', 'crabs', 'dammit', 'damn',
                           'darn', 'dirty', 'murder', 'omg', 'organ', 'organs', 'queer', 'sandler', 'sandlers',
                           'rum', 'strips', 'pots', 'sexes', 'psycho', 'beaver', 'willy', 'mick', 'aryan', 'dink',
                           'crackers', 'ugly', 'trashy', 'crappy', 'shitty', 'sucks', 'stupid', 'tart'])

# Offensive phrases which aren't in offensive_phrases_preprocessed.txt, that you want to add
# These should be lowercase, but they can contain punctuation
# You might want to add both singular and plural versions
ADD_TO_BLACKLIST = set(['pornhub', 'penises', 'suicide', 'suicides', 'marijuana', 'poo', 'blood', 'stripper',
                        'strippers', 'sexually', 'my balls', 'his balls', 'no balls', 'pornographic', 'abortion',
                        'torture', 'tortures', 'killed', 'killer', 'talk dirty', 'dirty talk', 'talking dirty',
                        'dirty talking', 'prostitution', 'urinate', 'mating', 'feces', 'swine', 'excreted' ,'excrete'])


# Inoffensive phrases that we don't want to classify as offensive, even though they contain a blacklisted phrase.
# For example we don't want to classify 'kill bill' as offensive, but we don't want to remove 'kill' from the blacklist.
# These phrases will be removed from text before the text is checked for offensive phrases.
# These phrases should be lowercase.
# These phrases might be said by the bot, so they need to be inoffensive enough for us to say.
WHITELIST_PHRASES = set(['kill bill', 'beavis and butt head', 'beavis and butt-head', 'beavis and butthead',
                         'kill a mockingbird', 'killer mockingbird', 'bloody mary', 'mick jagger', 'the mick',
                         "dick's sporting goods", 'lady and the tramp', 'jackson pollock', 'on the basis of sex',
                         'sex and the city', 'sex education', 'willy wonka and the chocolate factory', 'lady and the tramp', 
                         'suicide squad', "hell's kitchen", 'hells kitchen', 'jane the virgin',
                         'harry potter and the half blood prince', 'to kill a mockingbird', 'rambo last blood',
                         'shits creek', 'shit\'s creek', 'looney tunes', 'sniper', 'punky brewster',
                         'the good the bad and the ugly', 'pee wee herman', 'the ugly dachshund', 'xxx tentacion',
                         'lil uzi vert', 'lil uzi', 'young blood', 'chicken pot pie', 'pot roast', 'pop tarts',
                         'they suck', 'he\'s sexy', 'she\'s sexy', 'vegas strip', 'hell comes to frogtown',
                         'dick van dyke', 'blood and bullets', 'blood prison', 'dick powell'])

class OffensiveClassifier(object):
    """A class to load, and check text against, our preprocessed offensive phrases file"""

    preprocessed_blacklist_file = os.path.join(os.path.dirname(__file__), 'data_preprocessed/offensive_phrases_preprocessed.txt')

    def __init__(self):
        """
        Load the preprocessed blacklist from file. The blacklist is lowercase and already contains alternative versions
        of offensive phrases (singulars, plurals, variants with and without punctuation).
        """
        self.blacklist = load_text_file(self.preprocessed_blacklist_file)  # set of lowercase strings
        self.blacklist = self.blacklist.difference(REMOVE_FROM_BLACKLIST)
        self.blacklist = self.blacklist.union(ADD_TO_BLACKLIST)
        self.blacklist_max_len = max({len(phrase.split()) for phrase in self.blacklist})

    def contains_offensive(self, text: str, log_message: str = 'text "{}" contains offensive phrase "{}"') -> bool:
        """
        Returns True iff text contains an offensive phrase.
        """
        # Lowercase
        text = text.lower().strip()

        # Remove whitelisted phrases from text
        for whitelisted_phrase in WHITELIST_PHRASES:
            if whitelisted_phrase in text:
                logger.debug(f'Removing whitelisted phrase "{whitelisted_phrase}" from text "{text}" before checking for offensive phrases')
                text = text.replace(whitelisted_phrase, '').strip()

        # List of variants of text to check
        texts = set()

        # Remove special characters the same way the Amazon code does (leaving * and ' in)
        texts.add(text.translate({ord(p): '' for p in SPECIAL_CHARS}))

        # Remove all string.punctuation, replacing with ''.
        # Unlike the Amazon code, this will catch things like "pissin'".
        # "pissin" and "pissing" are in our blacklist, but "pissin'" is not.
        texts.add(text.translate({ord(p): '' for p in string.punctuation}))

        # Remove all string.punctuation, replacing with ' '.
        # This will catch things like "fuck-day" or "shit's" where we have an offensive word ("fuck", "shit") connected
        # via punctuation to a non-offensive word ("day", "s"), and the compound is not in our blacklist.
        texts.add(' '.join(text.translate({ord(p): ' ' for p in string.punctuation}).split()))

        # Also check the original text with no punctuation removed
        # This will catch things like "a$$" which are on our blacklist.
        # However, it won't catch "a$$" if it occurs next to non-whitespace e.g. "I love a$$."
        texts.add(text)

        # Check all the variants
        for text in texts:
            if contains_phrase(text, self.blacklist, log_message, lowercase_text=False, lowercase_phrases=False,
                               remove_punc_text=False, remove_punc_phrases=False, max_phrase_len=self.blacklist_max_len):
                return True
        return False


OFFENSIVE_CLASSIFIER = OffensiveClassifier()


def contains_offensive(text: str, log_message: str = 'text "{}" contains offensive phrase "{}"'):
    """
    Checks whether the text contains any offensive phrases on our blacklist.

    Inputs:
        text: the text to check. it will be lowercased and we will try various ways of removing punctuation to check
            against the blacklist.
        log_message: a str to be formatted with (text, offensive_phrase). An informative log message when the result is
            True. If empty, no log message will be shown.
    Returns: True iff text contains an offensive phrase
    """
    return OFFENSIVE_CLASSIFIER.contains_offensive(text, log_message)


if __name__ == "__main__":
    # You can test the contains_offensive function with the code below

    import time

    # Setup logging
    from chirpy.core.logging_utils import setup_logger, LoggerSettings

    LOGTOSCREEN_LEVEL = logging.DEBUG
    logger_settings = LoggerSettings(logtoscreen_level=LOGTOSCREEN_LEVEL, logtoscreen_usecolor=True,
                                     logtofile_level=None, logtofile_path=None,
                                     logtoscreen_allow_multiline=True, integ_test=False, remove_root_handlers=False)
    setup_logger(logger_settings)

    texts = ["my dick", "i went to dick's sporting goods"]

    for text in texts:
        print()
        t0 = time.time()
        label = contains_offensive(text)
        time_taken = time.time() - t0
        print(label, time_taken, text)