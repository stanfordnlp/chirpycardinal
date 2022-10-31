"""Functions for fetching wikipedia data from dynamodb / elasticsearch for entity linking"""

import logging
import boto3
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection, ElasticsearchException
from typing import List, Dict, Set, Optional
import os

from chirpy.core.latency import measure
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.entity_linker.lists import MANUAL_SPAN2ENTINFO, MANUAL_TALKABLE_NAMES
from chirpy.core.flags import inf_timeout, use_timeouts
from chirpy.core.util import query_es_index, get_es_host, get_elasticsearch

logger = logging.getLogger('chirpylogger')

MAX_ES_SEARCH_SIZE = 1000

ANCHORTEXT_QUERY_TIMEOUT = 3.0  # seconds
ENTITYNAME_QUERY_TIMEOUT = 1.0  # seconds

ARTICLES_INDEX_NAME = 'enwiki-20201201-articles'

# These are the fields we DO want to fetch from ES
FIELDS_FILTER = ['doc_title', 'doc_id', 'categories', 'pageview', 'linkable_span_info', 'wikidata_categories_all', 'redirects', 'plural']

# Entities with any of these wikidata classes are filtered out
UNTALKABLE_WIKIDATA_CLASSES = ['catalog of works', 'Wikimedia list article', 'Wikimedia disambiguation page',
                               'sports season', 'Wikimedia internal item']

# Ethan trying to remove false positives for weird entities
UNTALKABLE_WIKIDATA_CLASSES += ['social issue', 'criterion',
                                'disease', # Gout, False memory
                                'crime',
                                'artistic profession', # Pianist
                                'weapon',
                                'firearm',
                                'lighting' # Electric lamp
                               ]

UNTALKABLE_CLASSES_FILEPATH = os.path.join(os.path.dirname(__file__), 'untalkable_wikidata_classes.txt')
with open(UNTALKABLE_CLASSES_FILEPATH, 'r') as f:
    UNTALKABLE_WIKIDATA_CLASSES += [line.strip() for line in f.readlines()]

UNTALKABLE_CATEGORIES = ['Race (human categorization)']

WHITELIST_IN_UNTALKABLE_CLASSES = ['Coronavirus', 'Great Wall', 'Cat', 'Giant panda']

BLACKLIST_ENTITIES = ['Andijan']

# Elastic Search
es = get_elasticsearch()

def clean_category(category: str) -> str:
    """Clean the wikipedia category"""
    # It seems that sometimes the article title is included after | in the category. Get rid of this.
    if '|' in category:
        category = category[:category.index('|')]
    return category.strip()


def should_remove_wikidata_category(wikidata_category: List[str]) -> List[str]:
    """Returns True if we don't want to put the category in the WikiEntity object (because it's not useful information)"""
    if 'Wikimedia' in wikidata_category:
        return True
    if 'Wikidata' in wikidata_category:
        return True
    return False


def result2entity(result: dict) -> Optional[WikiEntity]:
    """
    Given a result from the ES "articles" index, process into a WikiEntity.
    Returns None if the result is a not talkable article (e.g. list pages, disambiguation pages)
    """
    source = result['_source']
    logging.warning(f"Source is {source}")
    wikidata_categories = source.get('wikidata_categories_all', set())
    categories = source.get('categories', set())

    # Return None for untalkable entities
    bad_wikidata_categories = [c for c in wikidata_categories if c in UNTALKABLE_WIKIDATA_CLASSES]
    bad_categories = [c for c in categories if c in UNTALKABLE_CATEGORIES]
    bad_taxa = [c for c in categories if c.startswith('Taxa named')] if len(source['doc_title'].split()) > 1 else [] # hack to avoid things like Horse — Ethan
    if (any([bad_wikidata_categories, bad_categories, bad_taxa]) and source['doc_title'] not in WHITELIST_IN_UNTALKABLE_CLASSES):
        logger.warning(f"Wasn't able to load data for {source['doc_title']} because it was banned due to: {bad_wikidata_categories} {bad_categories} {bad_taxa}")
        return None
    if (source['doc_title'] in BLACKLIST_ENTITIES):
        logger.warning(f"Wasn't able to load data for {source['doc_title']} because it is a blacklisted entity")
        return None

    # Filter wikidata_categories
    wikidata_categories = {s for s in wikidata_categories if not should_remove_wikidata_category(s)}

    anchortext_counts = {}
    for anchortext, count in source['linkable_span_info']:
        if anchortext in anchortext_counts:
            anchortext_counts[anchortext] += count
        else:
            anchortext_counts[anchortext] = count

    plural = source.get('plural', source['doc_title'])
    if plural.strip() == "":
        plural = source['doc_title']
    plural = MANUAL_TALKABLE_NAMES.get(source['doc_title'].lower(), plural)
    logger.primary_info(f"Plural of {source['doc_title']} is: {plural}")
    return WikiEntity(name=source['doc_title'], doc_id=int(source['doc_id']), pageview=source['pageview'], confidence=1,
                      wikidata_categories=wikidata_categories,anchortext_counts=anchortext_counts, redirects=source['redirects'],
                      plural=plural)

@measure
def make_wikientities(results: List[Dict]) -> List[WikiEntity]:
    """Given results from ES query to articles index, convert to WikiEntities"""
    entities = [result2entity(result) for result in results]  # list of WikiEntities / Nones
    return [ent for ent in entities if ent]  # filter out Nones


@measure
def get_entities_by_anchortext(spans: List[str], *, asr_entity_info: Dict[str, Dict[str, Dict[str, float]]] = {})  \
        -> Set[WikiEntity]:
    """
    Given a set of spans, query the ES "articles" index to get all WikiEntities with at least one of the spans in its
    anchortexts.

    Optionally, also consider entities from ASR correction, in the form of a dict from span to dictionaries containing
    entity names and ASR-corrected entity counts (count * ASR similarity).

    Returns:
        a set of WikiEntities. Each one has at least one span in spans in its anchortexts.
    """
    if not spans:
        return set()

    # Compose an ES query
    spans = list(set(spans))  # remove duplicates
    logger.info(f'Querying "{ARTICLES_INDEX_NAME}" ES index with these {len(spans)} spans: {spans}')
    match_oneof_spans_query = {'terms': {'linkable_span': spans}}
    query_should_clause = [match_oneof_spans_query]

    # Get any manual span -> entity links, and add them to the query
    manual_span2entname = {span: MANUAL_SPAN2ENTINFO[span].ent_name for span in spans if span in MANUAL_SPAN2ENTINFO}
    if manual_span2entname:
        logger.info('Getting the entities specified by these manual links:\n{}'.format(
            '\n'.join('"{}" -> "{}"'.format(span, ent_name) for span, ent_name in manual_span2entname.items())))
        match_oneof_entnames_query = {'terms': {'doc_title': list(manual_span2entname.values())}}
        query_should_clause.append(match_oneof_entnames_query)

    # Query ES
    query = {'query': {'bool': {'should': query_should_clause}}, 'sort': {'pageview': 'desc'}}
    results = query_es_index(es, ARTICLES_INDEX_NAME, query, size=MAX_ES_SEARCH_SIZE, timeout=ANCHORTEXT_QUERY_TIMEOUT, filter_path=['hits.hits._source.{}'.format(field) for field in FIELDS_FILTER])

    # Process into WikiEntities
    entities = make_wikientities(results)
    entname2ent = {ent.name: ent for ent in entities}

    # For manual links, add a spancount of 1 to the entity if necessary
    for span, ent_name in manual_span2entname.items():
        if ent_name not in entname2ent:
            logger.error(f'span "{span}" has a manual link to "{ent_name}" but was unable to find this entity in ES "{ARTICLES_INDEX_NAME}" index')
        else:
            ent = entname2ent[ent_name]
            if span not in ent.anchortext_counts:
                logger.info(f'span "{span}" has a manual link to "{ent_name}", which doesn\'t have "{span}" in its anchortexts, so adding a count of 1')
                span_counts = ent.anchortext_counts
                span_counts[span] = 1
                entname2ent[ent_name] = WikiEntity(ent.name, ent.doc_id, ent.pageview, ent.wikidata_categories, span_counts, ent.redirects)

    # Log and return
    logger.info("Got {} WikiEntities:\n{}".format(len(entname2ent), '\n'.join(repr(entname2ent[ent_name]) for ent_name in sorted(entname2ent.keys()))))
    return set(entname2ent.values())


@measure
def get_entities_by_wiki_name(wiki_names: List[str]) -> Dict[str, WikiEntity]:
    """
    Given a list of wiki doc titles, query the ES articles index to get the corresponding WikiEntities.
    Logs an error if any of the titles are NOT found.

    Returns:
        entname2ent: a dictionary mapping from entity name to WikiEntity
    """

    # Query ES
    wiki_names = list(set(wiki_names))
    logger.info(f'Querying "{ARTICLES_INDEX_NAME}" ES index with these {len(wiki_names)} wiki names: {wiki_names}')
    query = {'query': {'bool': {'must': [{'terms': {'doc_title': wiki_names}}]}}}
    results = query_es_index(es, ARTICLES_INDEX_NAME, query, size=MAX_ES_SEARCH_SIZE, timeout=ENTITYNAME_QUERY_TIMEOUT, filter_path=['hits.hits._source.{}'.format(field) for field in FIELDS_FILTER])

    # Process into WikiEntities
    entities = make_wikientities(results)
    entname2ent = {ent.name: ent for ent in entities}
    logger.info("Got {} WikiEntities:\n{}".format(len(entname2ent), '\n'.join(
        repr(entname2ent[ent_name]) for ent_name in sorted(entname2ent.keys()))))

    # Check if any are missing
    for wiki_name in wiki_names:
        if wiki_name not in entname2ent:
            logger.warning(f"Unable to fetch wiki_name from ES '{ARTICLES_INDEX_NAME}' index \n wiki_name ='{wiki_name}'")

    return entname2ent


# if __name__ == "__main__":
#
#     # Demo:
#
#     entities = get_entities_by_anchortext(['France', 'Japan'])
#     print(entities)
#
#     entities = get_entities_by_wiki_name(['france', 'japanese'])
#     print(entities)
