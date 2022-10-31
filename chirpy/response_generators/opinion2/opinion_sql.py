import logging
from functools import lru_cache
from chirpy.core.latency import measure
import re
import psycopg2
from typing import List, Optional, Set, Tuple
from dataclasses import dataclass
import os

import chirpy.core.blacklists.blacklists as blacklists
# import chirpy.core.offensive_classifier.offensive_classifier
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive

# host_stream = 'localhost'

host_stream = os.environ.get('POSTGRES_HOST', 'localhost')
port = 5432
database = 'twitter_opinions'
user = os.environ.get('POSTGRES_USER')
password = os.environ.get('POSTGRES_PASSWORD')

NOT_ALPHA_NUMERIC_RE = r'[^a-zA-Z0-9\s]'
HASHTAG = r'#[^\s]+'
AT_MENTION = r'@[^\s]+'
AMP = r'&amp'

logger = logging.getLogger('chirpylogger')

@dataclass(frozen=False, eq=True, unsafe_hash=True)
class Phrase:
    text : str
    category : Optional[str]
    wiki_entity_name : Optional[str]
    wiki_category : Optional[str]
    good_for_wiki : bool
    generic : bool

    @staticmethod
    def from_row(row : List[str]):
        text, category, wiki_entity_name, wiki_category, good_for_wiki, generic = row
        return Phrase(text, category, wiki_entity_name, wiki_category, good_for_wiki, generic)

@dataclass(frozen=True, eq=True)
class Opinion:
    entity : str
    reason : str
    attitude : str
    sentiment : int # 0 - negative, 4 - positive

def fetch_sql(sql_statement, args=None):
    """

    :param sql_statement: SQL query
    :param args: tuple
    :return:
    """
    print(host_stream, port, database, user, password)
    conn = psycopg2.connect(host=host_stream, port=port, database=database, user=user, password=password)
    cur = conn.cursor()
    if args is None:
        cur.execute(sql_statement)
    else:
        cur.execute(sql_statement, args)
    result = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return result

def parse_entry(entry : Tuple[str, str, str, str]) -> Opinion:
    """This method parses a specific entry returned which is a list in the form of
    [entity, reason, attitude, sentiment]

    :param entry: a entry returned from SQL in the form of [entity, reason, attitude, sentiment]
    :type entry: List[str]
    :return: an entity object
    :rtype: Opinion

    >>> entry = ('cats', 'cats cute', 'like', 'positive')
    >>> parse_entry(entry)
    Opinion(entity='cats', reason='cats cute', attitude='like', sentiment=1)
    """
    entity, reason, attitude, sentiment = entry
    reason = re.sub(HASHTAG, '', reason) # remove all hashtags
    reason = re.sub(AT_MENTION, '', reason) # remove all mentions
    reason = re.sub(AMP, '', reason) # remove amp at the end of reasons
    reason = re.sub(NOT_ALPHA_NUMERIC_RE, '', reason) # remove non-alphanumeric characters
    reason = re.sub('httpst', '', reason).strip() # remove trailing httpst
    numeric_sentiment = 0 if sentiment == 'negative' else 4
    return Opinion(entity, reason, attitude, numeric_sentiment)

MANUAL_REMOVE = ['Football', 'Sport', 'Sleep', 'Unicorn', 'being alone', 'kids', 'taking naps', 'being home alone', 'youtube', 'waking up early', 'going to work', 'being sad', 'online shopping', 'animals']
def filter_entries(entries):
    return [phrase for phrase in entries if (phrase.wiki_entity_name not in MANUAL_REMOVE and phrase.text not in MANUAL_REMOVE and not phrase.text.startswith("to"))]

@lru_cache(maxsize=128)
@measure
def get_opinionable_phrases() -> List[Phrase]:
    entries = fetch_sql("select phrase, category, wiki_entity_name, wiki_category, good_for_wiki, generic from labeled_phrases_cat;")
    entries = [Phrase.from_row(entry) for entry in entries]
    entries = filter_entries(entries)
    return entries

@lru_cache(maxsize=128)
@measure
def get_opinions(phrase : str) -> Set[Opinion]:
    """This method takes in an phrase and return a set of opinions

    :param phrase: the opinionable phrase that we have identified
    :type phrase: str
    :return: a list of opinions that are not offensive
    :rtype: Set[Opinion]
    """
    query = "select distinct phrase, reason, attitude, sentiment from labeled_opinions where phrase = %s and reason_appropriateness = 4"
    results = fetch_sql(query, (phrase,))
    opinions = set(parse_entry(entry) for entry in results)
    opinions = set(opinion for opinion in opinions if not contains_offensive(opinion.reason))
    opinions = set(opinion for opinion in opinions if 'i love money' not in opinion.reason)
    return opinions
