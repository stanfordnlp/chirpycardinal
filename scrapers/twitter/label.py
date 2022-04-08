import bz2
import csv
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
import psycopg2 # type: ignore
import argparse
import os
from ast import literal_eval
from collections import Counter
from dataclasses import dataclass
from chirpy.core.util import get_es_host

# FOR HAOJUN
# DUMP_PATH = /Users/haojun/Downloads/opinions_04_09_2020_shuffled.txt.bz2'

parser = argparse.ArgumentParser()
parser.add_argument('annotator', type=str, help='The name of the annotator')
parser.add_argument('dump_path', type=str, help='The fully qualified path of the .bz file')
parser.add_argument('--entity_path', type=str, default=None, help='A path to a list of entities. If a CSV file we take the first column')
ANNOTATOR = parser.parse_args().annotator
DUMP_PATH = parser.parse_args().dump_path
CATEGORIES = {1: 'Offensive', 2: 'Incomprehensible', 3: 'Ok', 4: 'I want Alexa to say this'}

host = get_es_host("postgres")
host_stream = get_es_host("chirpy_stream")
port = os.environ.get("POSTGRES_PORT")
database = 'twitter_opinions'
user = 'postgres'
password = os.environ.get('POSTGRES_PW')

@dataclass
class LabeledOpinion(object):
    id : str
    entity : str
    reason : str
    attitude : str
    sentiment : str
    reason_appropriateness : int
    tweet_id : int
    annotator : str

@dataclass
class AnnotatorOpinions:
    id : str
    annotator : str
    entity : str
    entity_appropriate : bool
    sentiment : str

def fetch_sql(sql_statement, host):
    print(sql_statement)
    conn = psycopg2.connect(host=host, port=port, database=database, user=user, password=password) # type: ignore
    cur = conn.cursor()
    cur.execute(sql_statement)
    result = cur.fetchall()
    conn.commit()
    cur.close()
    return result

def insert_opinion(args, host):
    conn = psycopg2.connect(host=host, port=port, database=database, user=user, password=password) # type: ignore
    cur = conn.cursor()
    insert = f"""
        insert into labeled_opinions (phrase, reason, attitude, sentiment, reason_appropriateness, tweet_id, annotator, creation_date_time)
        values (%s, %s, %s, %s, %s, %s, '{ANNOTATOR}', CURRENT_TIMESTAMP)
    """
    cur.execute(insert, args)
    conn.commit()
    cur.close()
    return

def insert_annotator(args, host):
    conn = psycopg2.connect(host=host, port=port, database=database, user=user, password=password) # type: ignore
    cur = conn.cursor()
    insert = f"""
        insert into annotator_opinions (annotator, entity, entity_appropriate, sentiment, creation_date_time)
        values ('{ANNOTATOR}', %s, %s, %s, CURRENT_TIMESTAMP)
    """
    cur.execute(insert, args)
    conn.commit()
    cur.close()
    return

def done(entity, sentiment):
    return (entity, sentiment, 4) in COUNTER and COUNTER[(entity, sentiment, 4)] >= 4 and sum(COUNTER[(entity, sentiment, approps)] for approps in range(1, 6)) > 20

def label():
    with bz2.open(DUMP_PATH, 'rt') as f:
        while True:
            (entity, sentiment), tweets = literal_eval(f.readline())
            if ENTITIES_TO_WHITELIST is not None and entity not in ENTITIES_TO_WHITELIST:
                continue
            while entity not in set([annotator_opinion.entity for annotator_opinion in annotator_opinions]) and \
                    entity not in not_appropriate_entities:
                print(f'>> What is your sentiment on \033[92m{entity}\033[00m? (positive or negative or neutral), type "inapprop" if it is inappropriate, "exit" to exit')
                feedback = input(f'? ')
                if feedback == 'positive':
                    insert_annotator((entity, True, feedback), host_stream)
                    annotator_opinions.append(AnnotatorOpinions('', ANNOTATOR, entity, True, feedback))
                elif feedback == 'negative':
                    insert_annotator((entity, True, feedback), host_stream)
                    annotator_opinions.append(AnnotatorOpinions('', ANNOTATOR, entity, True, feedback))
                elif feedback == 'neutral':
                    insert_annotator((entity, True, feedback), host_stream)
                    annotator_opinions.append(AnnotatorOpinions('', ANNOTATOR, entity, True, feedback))
                elif feedback == 'inapprop':
                    insert_annotator((entity, False, None), host_stream)
                    not_appropriate_entities.add(entity)
                elif feedback == 'exit':
                    return
            if entity in not_appropriate_entities:
                print(f'>> Skipping \033[91m{entity}\033[00m because it is inappropriate')
                continue
            if done(entity, sentiment):
                print(f'>> Skipping \033[91m{entity}, {sentiment}\033[00m because we already have enough')
                continue
            print(f'>>>>>> Begin new phrase \033[91m{entity}, {sentiment}\033[00m')  
            for tweet in tweets:
                if done(entity, sentiment):
                    break
                reason, _, attitude, _, tweet_id = tweet
                if reason in labeled_reasons:
                    continue
                if len(reason.split(' ')) < 5 or contains_offensive(reason):
                    continue
                feedback = ''
                while not ((feedback.isdigit() and int(feedback) <= 4 and int(feedback) >= 1) or feedback == 'exit'):
                    opposite_attitude = 'like' if attitude in ['hate', 'dislike', "don't like"] else "don't like"
                    good_counters = COUNTER[(entity, sentiment, 4)]
                    current_counters = sum(COUNTER[(entity, sentiment, feedback)] for feedback in range(1, 5))
                    print(f'>  i \033[93m{opposite_attitude} \033[92m{entity}\033[00m but (i feel like, because) \033[96m{reason}\033[00m ({good_counters}/{current_counters}/{len(tweets)})')
                    category_string = '; '.join([f'[{key}] {val}' for key, val in CATEGORIES.items()])
                    print(f'Select from {category_string}, or "exit" to exit')
                    feedback = input(f'? ')
                if (feedback.isdigit() and int(feedback) <= 4 and int(feedback) >= 1):
                    insert_opinion((entity, reason, attitude, sentiment, feedback, tweet_id), host_stream)
                    COUNTER[(entity, sentiment, int(feedback))] += 1
                elif feedback == 'exit':
                    return

if __name__ == "__main__":
    if parser.parse_args().entity_path is not None:
        with open(parser.parse_args().entity_path, 'r') as f:
            ENTITIES_TO_WHITELIST = [row[0] for row in list(csv.reader(f))[1:]]
    else:
        ENTITIES_TO_WHITELIST = None
    already_labeled = [LabeledOpinion(*row[:-1]) for row in fetch_sql(
    f"SELECT * from labeled_opinions where annotator='{ANNOTATOR}' and creation_date_time > timestamp '2020-05-25 00:00:00';", host_stream)]
    not_appropriate_entities = set([row[0] for row in fetch_sql(
        f"select distinct entity from annotator_opinions where entity_appropriate = false and annotator='{ANNOTATOR}';", host_stream)])
    annotator_opinions = [AnnotatorOpinions(*row[:-1]) for row in fetch_sql(
        f"select * from annotator_opinions where annotator = '{ANNOTATOR}'", host_stream)]
    labeled_reasons = set([labeled_opinion.reason for labeled_opinion in already_labeled])
    COUNTER = Counter([(labeled_opinion.entity, labeled_opinion.sentiment, labeled_opinion.reason_appropriateness) for labeled_opinion in already_labeled])
    label()

# TEST_INSERT = """
# insert into labeled_opinions (entity, reason, attitude, sentiment, appropriate_entity, reason_appropriateness, tweet_id, creation_date_time)
# values ('cats', 'they have a soft and pretty coat!', 'like', 'positive', true, 5, NULL, CURRENT_TIMESTAMP)
# """
# execute_sql(TEST_INSERT)