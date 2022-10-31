import re
import boto3
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection
import logging
import random

from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.entity_linker.wiki_data_fetching import get_entities_by_wiki_name
from chirpy.annotators.sentseg import NLTKSentenceSegmenter

logger = logging.getLogger('chirpylogger')

host = 'search-default-nfnpn4os4ajabsvj6ts3cfl3vy.us-east-1.es.amazonaws.com' # the Amazon ES domain, with https://
# host = 'search-en-wiki2-a3bimhsymud77u4lkr2py4cpeq.us-east-1.es.amazonaws.com'
region = 'us-east-1' # e.g. us-west-1
service = 'es'

es = Elasticsearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth=('chirpy', 'Chirpy2020!'),
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection,
    timeout=2,
)

INDEX='enwiki-20201201-sections'

def prune_section(section):
    return section['text'][0] in {'†', '+', '*'}

def prune_text(text):
    return sum(1 if x in text else 0 for x in {'|', '[', ']'}) != 0

def get_related_candidate_entities(ent_name):
    query = {'query': {'bool': {'filter': [
            {'term': {'doc_title': ent_name}}]}}}
    sections = es.search(index=INDEX, body=query, size=100)
    links, text = set([]), set([])
    for section in sections['hits']['hits']:
        source = section['_source']
        if (source['title'].lower() == '' or source['title'].lower() == 'cuisine') and not prune_section(source):
            source_text = source['text'].split('\n\n')
            for st in source_text:
                if not prune_text(st):
                    text.add(st)
                    links.update(source['wiki_links'])

    links, text = list(links), '\n'.join(list(text))
    ents = []
    type2ent = {'book_related':[], 'location_related':[], 'food_related':[], 'sport_related':[], 'film':[]}
    if len(links) > 0:
        ents = list(get_entities_by_wiki_name(links).values())
        for et in type2ent:
            try:
                expected_type = getattr(ENTITY_GROUPS_FOR_EXPECTED_TYPE,et)
                type2ent[et] = [e for e in ents if expected_type.matches(e)]
            except:
                logger.error(f"Expected type: {et} doesn't exist")

    return type2ent, text

def get_transitions(ent_name):
    sentseg = NLTKSentenceSegmenter(None)
    type2ent, text = get_related_candidate_entities(ent_name)
    text_sentences = []
    sents = {}
    for et, ents in type2ent.items():
        if len(ents) > 0:
            best_ent = max(ents, key = lambda x: x.pageview)
            spans = list(best_ent.anchortext_counts.keys())[:3]
            if not text_sentences:
                text_sentences = list(sentseg.execute(text.lower()))
            for s in spans:
                # cand_sent = [ts for ts in text_sentences if s in ts]
                cand_sent = [ts for ts in text_sentences if re.search(fr"\b{s}\b", ts)]
                if len(cand_sent) > 0:
                    cand_sent = cand_sent[0]
                    cand_sent = re.sub(r"\([^()]*\)", "", cand_sent)
                    sents[et] = (best_ent, cand_sent)
                    break
    return sents

STARTER_TEXTS = ["did you know, ",
     "i recently learned that ",
     "i was reading recently and found out that ",
     "did you know that ",
     "i was interested to learn that "]

def get_random_starter_text():
    return random.choice(STARTER_TEXTS)
