"""This file is for generally useful functions"""
import re
import os
import csv
import time
import json
import unicodedata
import sys
from functools import lru_cache
from pathlib import Path

import boto3
import logging
import datetime
import pytz
from typing import List, Dict, Set, Optional, Iterable, Any, Callable
from chirpy.core.latency import measure
from random import choices
from elasticsearch import Elasticsearch, ElasticsearchException
from chirpy.core.flags import use_timeouts, inf_timeout

from chirpy.core.canary import is_already_canary

logger = logging.getLogger('chirpylogger')

dynamodb = boto3.client('dynamodb', region_name='us-east-1')

# Max number of keys to submit via dynamodb.batch_get_item()
MAX_DYNAMODB_BATCHSIZE = 100

# Dict mapping from Unicode codepoints (int) to None
PUNC_TABLE = dict.fromkeys(i for i in range(sys.maxunicode) if unicodedata.category(chr(i)).startswith('P'))

DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

CHIRPY_HOME = os.environ.get('CHIRPY_HOME', Path(__file__).parent.parent.parent)
config_fname = 'chirpy/core/es_config.json'
config_path = os.path.join(CHIRPY_HOME, config_fname)
NAME_2_ES_HOST = json.load(open(config_path, 'r'))

def get_es_host(name):
    if name in NAME_2_ES_HOST.keys():
        return NAME_2_ES_HOST[name]['url']
    else:
        return None
    

def get_elasticsearch():
    host = os.environ.get('ES_HOST', "localhost")
    port = os.environ.get('ES_PORT', "9200")
    scheme = os.environ.get('ES_SCHEME', 'http')
    username = os.environ.get('ES_USER')
    password = os.environ.get('ES_PASSWORD')
    return Elasticsearch([{'host': host, 'scheme': scheme, 'port': port}], http_auth=(username, password), timeout=99999)


def get_user_datetime(user_timezone=None) -> Optional[datetime.datetime]:
    """
    Returns the datetime, now, in the user's timezone (which we got from their Alexa device id).

    If we don't have the user's timezone (including if it's not an Alexa device conversation, such as
    integration tests or interactive mode), returns None
    """
    if user_timezone is None:
        logger.info('user_timezone is None, so returning None as user datetime')
        return None
    try:
        logger.info(f"Getting the datetime now in the user's timezone: {user_timezone}")
        date_time = datetime.now(pytz.timezone(user_timezone))
        logger.info(f"The datetime now in the user's timezone is {date_time}")
        return date_time
    except:
        logger.error(f'Exception when trying to get user datetime. Returning None.', exc_info=True)
        return None



def get_user_dayofweek(user_timezone=None) -> Optional[str]:
    """Return the day of the week, now, in the user's timezone"""
    user_datetime = get_user_datetime(user_timezone)  # datetime/None
    if user_datetime is None:
        logger.info('user_datetime is None, so returning None as user day of week')
        return None
    return DAYS_OF_WEEK[user_datetime.weekday()]  # str


# # TODO: investigate whether this is slow enough to be a problem
# @measure
# def init_stemmer():
#     t0 = time.time()
#     stemmer = nltk.stem.snowball.EnglishStemmer()
#     logger.info('Time to init nltk stemmer: {} seconds'.format(time.time()-t0))
#     return stemmer
#
# stemmer = init_stemmer()
#
# def stem(text: str):
#     """Apply the nltk stemmer to each word in text"""
#     return ' '.join([stemmer.stem(t) for t in text.split()])


def normalize_dist(dist: dict):
    """
    Given dist, a dict mapping from keys to numbers, return a normalized version.
    """
    sum_values = sum(dist.values())
    if sum_values == 0:
        logger.error(f"Trying to normalize distribution {dist} which sums to 0. Returning original distribution.")
        return dist
    return {k: v / sum_values for k, v in dist.items()}


def sample_from_prob_dist_dict(prob_dist: dict):
    """
    Sample one item from a probability distribution and return it.

    :param prob_dist - a dictionary representing a probability distribution (mapping key -> float)
    :return: a sampled key from prob_dist
    """
    keys = [key for key in prob_dist.keys()]
    sample = choices(keys, [prob_dist[key] for key in keys])[0]
    return sample


def remove_punc(text: str, keep: List[str] = [], replace_with_space: List[str] = ['-', '/']):
    """
    Removes all Unicode punctuation (this is more extensive than string.punctuation) from text.
    Most punctuation is replaced by nothing, but those listed in replace_with_space are replaced by space.

    Solution from here: https://stackoverflow.com/questions/11066400/remove-punctuation-from-unicode-formatted-strings/11066687#11066687

    Inputs:
        keep: list of strings. Punctuation you do NOT want to remove.
        replace_with_space: list of strings. Punctuation you want to replace with a space (rather than nothing).
    """
    punc_table = {codepoint: replace_str for codepoint, replace_str in PUNC_TABLE.items() if chr(codepoint) not in keep}
    punc_table = {codepoint: replace_str if chr(codepoint) not in replace_with_space else ' ' for codepoint, replace_str
                  in punc_table.items()}
    text = text.translate(punc_table)
    text = " ".join(text.split()).strip()  # Remove any double-whitespace
    return text


def make_text_like_user_text(text: str):
    """Remove punctuation from the text so that it matches what we would get in a user utterance"""
    return remove_punc(text.lower().strip(), keep=["'"])


#TODO: Should probably be replaced by prettyprinting (using pprint)
def print_dict_linebyline(dictionary: dict):
    """Returns a string which shows each key/value pair on a new line"""
    if len(dictionary)>0:
        key_maxlen = max([len(repr(k)) for k in dictionary.keys()])
        val_maxlen = max([len(repr(v)) for v in dictionary.values()])
        return '\n'.join(["{0:>{1}}  {2}".format(repr(key), key_maxlen, repr(value)) for key, value in dictionary.items()])
    else:
        return '{}'


def sentence_join(sentence1: str, sentence2: str):
    """
    Checks if the first sentence ends in [.!?]. If not, adds a period before concatenating the two sentences.

    :param sentence1: First sentence to concatenate
    :param sentence2: Second sentence to concatenate
    :return: The two sentences concatenated with '.' added between if necessary
    """
    sentence1 = sentence1.strip()
    sentence2 = sentence2.strip()
    if sentence1[-1] not in ['.', '!', '?']:
        sentence1 += '.'
    return sentence1 + ' ' + sentence2


def catch_errors(default_output):
    """A decorator that catches any errors when executing func, logs an error and returns default_output instead"""
    def wrapper(func):
        def inner(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except:
                logger.error(f'Error when calling the function {func.__name__} with args={args} and kwargs={kwargs}, so returning default_output {default_output}', exc_info=True)
                return default_output
            return result
        return inner
    return wrapper

@measure
def query_es_index(es: Elasticsearch, index_name: str, query: dict, size: int, timeout: float,
                   filter_path: List[str] = []) -> List[dict]:
    """
    Send the query to the ES index, catch any errors and do sensible logging, and return the results.

    See here for more info: https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search

    Inputs:
        es: the Elasticsearch instance
        index_name: the name of the index you want to query
        query: your query
        size: max number of results
        timeout: timeout in seconds
        filter_path: if you only want some fields, specify them here.

    Returns:
        A list of results. If there's an error or a timeout, returns an empty list.
    """
    timeout = timeout if use_timeouts else inf_timeout
    logger.info(f"Querying ElasticSearch '{index_name}' index with timeout={timeout}s, size={size}, and this query: {query}")
    try:
        results = es.search(index=index_name, body=query, size=size, filter_path=filter_path,
                            request_timeout=timeout)
        # logger.debug('Query to ElasticSearch "{}" took {}ms'.format(index_name, results['took']))  # sometimes 'took' isn't in results, I'm not sure why
        if not results:
            return []
        return results['hits']['hits']
    except ElasticsearchException as e:
        logger.warning(f'When querying "{index_name}" index with timeout = {timeout} seconds, size={size}, and query={query},'
                       f'Elasticsearch returned the following exception:\n{e}.\nReturning empty list.')
        return []
    except Exception:
        logger.error(f'When querying "{index_name}" index with timeout = {timeout} seconds, size={size}, and query={query}'
                     f'Elasticsearch returned an exception.\nReturning empty list.', exc_info=True)
        return []


@measure
def load_text_file(filepath):
    """Loads a text file, returning a set where each item is a line of the text file"""
    t0 = time.time()
    lines = set()  # set of strings
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                lines.add(line)
    logger.info('Time to load {} lines from {}: {} seconds'.format(len(lines), filepath, time.time()-t0))
    return lines

def load_csv_file(filepath, delimiter=',') -> List[Dict]:
    """Loads a csv file, returning a list of rows, where each row is a dict mapping each header name to value"""
    rows = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            rows.append(row)
    return rows

@measure
def get_spoken_unigram_freq() -> Dict[str, int]:
    """
    Loads the spoken unigram frequencies from file. The unigrams are lowercased and have punctuation removed (to match
    user utterances).

    Returns:
        unigram2freq: dict mapping unigram (str) to freq (int)
    """
    t0 = time.time()
    filename = os.path.join(os.path.dirname(__file__), '../data/spoken_unigram_freqs.csv')
    rows = load_csv_file(filename)
    unigram2freq = {row['unigram']: int(row['freq']) for row in rows}
    logger.info('Time to load {} lines from {}: {} seconds'.format(len(unigram2freq), filename, time.time() - t0))
    return unigram2freq


def get_unigram_freq_fn():
    """
    Load the spoken unigram frequencies, and return a function that gives the frequency of any unigram.

    The function we return gives 0 for unigrams not in the data.
    Note: due to tokenization, the unigram freq data has "n't" and "do" as separate unigrams, and doesn't have "don't".
    When you give e.g. "don't" to the function, it will return the freq for "do".
    """
    unigram2freq = get_spoken_unigram_freq()
    apostrophe_unigrams = {unigram for unigram in unigram2freq.keys() if "'" in unigram}  # 'll, 's, n't, ...

    def get_freq(unigram) -> Optional[int]:

        # If unigram ends with an apostrophe_unigram, e.g. unigram="don't" ends with "n't",
        # return the freq of the first part, e.g. "do"
        if "'" in unigram:
            for apostrophe_unigram in apostrophe_unigrams:
                if unigram.endswith(apostrophe_unigram):
                    return get_freq(unigram[:-len(apostrophe_unigram)])

        if unigram in unigram2freq:
            return unigram2freq[unigram]
        return 0

    return get_freq


@lru_cache(maxsize=1024)
def get_ngrams(text, n):
    """
    Returns all ngrams that are in the text.
    Inputs:
      text: string, space-separated
      n: int
    Returns:
      list of strings (each is a ngram, space-separated)
    """
    tokens = text.split()
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-(n-1))]  # list of str


def contains_phrase(text: str, phrases: Set[str], log_message: str = 'text "{}" contains phrase {}',
                    lowercase_text: bool = True, lowercase_phrases: bool = True,
                    remove_punc_text: bool = True, remove_punc_phrases: bool = True,
                    max_phrase_len: Optional[int] = None):
    """
    Checks whether text contains any phrase in phrases.
    By default, the check is case blind (text and phrases are lowercased before checking).
    This function is optimized for when phrases is a large set (for each eligible ngram in text, we check if it's in
    phrases). If phrases is small and text is long, it might be more efficient to check, for each phrase, whether it's
    in text.

    Note, a phrase is "in" text iff the sequence of words in phrase is a subsequence of the sequence of words in text.
        if phrase="name" and text="my name is julie", result=True
        if phrase="name" and text="i collect ornaments", result=False
        if phrase="your name" and text="what is your name", result=True
        if phrase="your name" and text="my name is julie what is your favorite color", result=False

    Inputs:
        text: string, space-separated.
        phrases: set of strings, space-separated.
        log_message: If not empty, a str to be formatted with (text, phrase) that gives an informative log message when
            the result is True.
        lowercase_text: if True, text will be lowercased before checking.
        lowercase_phrases: if True, all phrases will be lowercased before checking.
        remove_punc_text: if True, punctuation will be removed from text before checking.
        remove_punc_phrases: if True, punctuation will be removed from phrases before checking.
        max_phrase_len: max len (in words) of the longest phrase in phrases. If None, this will be computed from phrases
    """
    if lowercase_text:
        text = text.lower()
    if lowercase_phrases:
        phrases = set([p.lower() for p in phrases])
    if remove_punc_text:
        text = remove_punc(text)
    if remove_punc_phrases:
        phrases = set([remove_punc(p) for p in phrases])
    if max_phrase_len is None:
        max_phrase_len = max((len(phrase.split()) for phrase in phrases))

    # For each ngram in text (n=1 to max_phrase_len), check whether the ngram is in phrases.
    # Even if phrases is very large, this fn is efficient because we only look up the (relatively few) ngrams in text,
    # rather than iterating through all of phrases. Note phrases is a set so checking membership is fast.
    length = len(text.split())
    for n in range(1, min(max_phrase_len, length)+1):
        ngrams = get_ngrams(text, n)
        for ngram in ngrams:
            if ngram in phrases:
                if log_message:
                    logger.info(log_message.format(text, ngram))
                return True
    return False


def replace_phrase(text: str, phrase_before: str, phrase_after: str, fix_multiple_spaces: bool = True) -> str:
    """
    Replaces phrase_before with phrase_after in text. phrase_before will only be replaced if it appears surrounded by
    word boundaries.

    e.g. replace_phrase('the cat is my favorite category of animals', 'cat', 'dog') -> 'the dog is my favorite category of animals'

    @param text: the text to be changed
    @param phrase_before: the phrase to be replaced
    @param phrase_after: the phrase to replace it with
    @param fix_multiple_spaces: if True, will replace any multiple spaces with single spaces after replacement
    @return: text, with phrase_before replaced with phrase_after
    """
    # If any of text, phrase_before or phrase_after are None, do nothing
    if text is None or phrase_before is None or phrase_after is None:
        return text

    text = re.sub(r'\b{}\b'.format(phrase_before), phrase_after, text)
    if fix_multiple_spaces:
        text = ' '.join(text.split())
    return text


def contains_substring(text: str, phrases: Set[str], log_message: str,
                       lowercase_text: bool = True, lowercase_phrases: bool = True):
    """
    Checks whether any of the strings in phrases are a substring of text.
    By default, the check is case blind (text and phrases are lowercased before checking).

    Inputs:
        text: string, space-separated.
        substrings: set of strings, space-separated. assumed to be lowercased.
        log_message: a str to be formatted with (text, phrase). Gives an informative log message when the result is True
        lowercase_text: if True, text will be lowercased before checking.
        lowercase_phrases: if True, all phrases will be lowercased before checking.
    """
    if lowercase_text:
        text = text.lower()
    if lowercase_phrases:
        phrases = set([p.lower() for p in phrases])
    for s in phrases:
        if s in text.lower():
            logger.primary_info(log_message.format(text, s))
            return True
    return False


def is_exactmatch(text: str, phrases: Set[str], log_message: str,
                  lowercase_text: bool = True, lowercase_phrases: bool = True):
    """
    Checks whether the text is an exact match with any string in phrases.
    By default, the check is case blind (text and phrases are lowercased before checking).

    Inputs:
        text: string, space-separated
        phrases: set of strings, space-separated. assumed to be lowercased.
        log_message: a str to be formatted with (text). Gives an informative log message when the result is True.
        lowercase_text: if True, text will be lowercased before checking.
        lowercase_phrases: if True, all phrases will be lowercased before checking.
    """
    if lowercase_text:
        text = text.lower()
    if lowercase_phrases:
        phrases = set([p.lower() for p in phrases])
    if text.lower() in phrases:
        logger.primary_info(log_message.format(text.lower()))
        return True
    return False

def filter_and_log(filter_function: Callable[[Any], bool], iterable: Iterable, iterable_name: str, reason_for_filtering:str, log_level=logging.DEBUG):
    # TODO: if you look at the many places we use contains_offensivephrase inside a list comprehension, they could be simplified by calling this function instead.
    #  It would be good to switch them over so that people are aware of this function and start using it. otherwise people will just keep calling contains_offensivephrase directly
    """
    Filter the iterable using the filter function and return the filtered iterable.
    Also log the filtered items with a reason for filtering
    Args:
        filter_function (Callable[[...], bool]): function which is applied to each element and returns true or false
        iterable (Iterable): iterable which is to be filtered
        iterable_name (str): name of iterable, used for logging
        reason_for_filtering (str): reason for filtering, used for logging
        log_level: optional log_level to log to a specific level

    Returns:
        List: list of filtered elements
    """
    true_iter = []
    false_iter = []
    for i in iterable:
        if filter_function(i):
            true_iter.append(i)
        else:
            false_iter.append(i)
    if false_iter:
        logger.log(log_level, f"Filtered out {false_iter} from {iterable_name} because {reason_for_filtering}")
    return true_iter


class HDict(dict):
    def __hash__(self):
        return hash(frozenset(self.items()))


def get_function_version_to_display(event) -> Optional[str]:
    """
    Returns a string to represent the version of the code, given the event and context supplied by AWS Lambda.
    If we're in MAINLINE, return mainline_{commit_id}
    If we're in DEV, return dev_canary_{commit_id} if it's a canary conversation and dev_{commit_id} if not.
    Otherwise return None.
    """
    pipeline = os.environ.get('PIPELINE', '')
    commit_id = os.environ.get('COMMITID', '')
    stage = os.environ.get('STAGE', '')
    if pipeline == 'DEV':
        if not commit_id:
            logger.error('COMMITID environment variable is empty')
        if is_already_canary(event):
            return 'dev_canary_{}'.format(commit_id[:8])
        else:
            return 'dev_{}'.format(commit_id[:8])
    elif pipeline == 'MAINLINE':
        if not commit_id and stage == 'PROD':
            logger.error('COMMITID environment variable is empty')
        return 'mainline_{}'.format(commit_id[:8])
    else:
        return None


def get_eastern_us_time() -> datetime.datetime:
    """Returns the US Eastern time now"""
    return datetime.datetime.now(pytz.timezone('US/Eastern'))

def get_eastern_dayofweek() -> str:
    return DAYS_OF_WEEK[get_eastern_us_time().weekday()]  # str

def get_pacific_us_time() -> datetime.datetime:
    """Returns the US Pacific time now"""
    return datetime.datetime.now(pytz.timezone('US/Pacific'))

def get_pacific_dayofweek() -> str:
    return DAYS_OF_WEEK[get_pacific_us_time().weekday()]  # str


@measure
def run_module(module, function_name, args: List=[], kwargs: Dict={}):
    task = getattr(module, function_name)(*args, **kwargs)
    return task

@measure
def initialize_module(module_class, args: List=[], kwargs: Dict={}):
    initialized_module = module_class(*args, **kwargs)
    return initialized_module
