from collections import defaultdict
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import json
import logging
from metaphone import doublemetaphone
import os
from typing import Dict, List, Optional  # NOQA

from chirpy.core.asr.index_phone_to_ent import PHONE_TO_ENT_INDEX, span_to_phoneme_string
from chirpy.core.asr.lattice import span_to_lattice, get_lattice_similarity, remove_stress
from chirpy.core.entity_linker.lists import get_unigram_freq, DONT_LINK_WORDS
from chirpy.core.latency import measure
from chirpy.core.util import query_es_index, get_es_host, get_elasticsearch

logger = logging.getLogger('chirpylogger')

SIMILARITY_RATIO_THRESHOLD = 0.8  # cutoff for the similarity score

ES_QUERY_TIMEOUT = 2.0  # seconds

host = "localhost"
port = "9200"
username = os.environ.get('ES_USER')
password = os.environ.get('ES_PASSWORD')

es = get_elasticsearch()

@measure
def get_asr_aware_span2entsim(spans: List[str], g2p_module, topn: int = 200) -> Dict[str, Dict[str, Dict]]:
    """
    Takes a list of spans, convert them into their phonetic representations, and search in the PHONE_TO_ENT_INDEX for
    topn most similar sounding anchortexts as well as the Wikipedia entities they correspond to.

    @param spans: list of strings
    @param topn: max number of anchortext candidates to consider for all spans
    @param g2p_module: remote module for grapheme to phoneme
    @return: span2entsim. dict mapping a user utterance span (string) to a "ent2sim" dict which maps an anchortext
        (string) to a dictionary, which contains two keys:
        - similarity, which maps to the phonetic similarity scores (float) between the anchortext and the utterance span
          (which is always between 0 and 1).
        - entnames, which maps to a list of entity names with this anchortext links to
    """

    logger.debug(f"Got these spans as candidates for ASR-aware entity linking: {spans}")

    span2entsim = defaultdict(lambda: defaultdict(dict))

    # filter out spans that are substrings of other spans
    spans_for_query = [span for span in spans if len([x for x in span.split() if x in DONT_LINK_WORDS]) / len(span.split()) < .67]

    queries_to_keep = 3
    if len(spans_for_query) > queries_to_keep:
        # prioritize spans with more rare words
        spans_for_query = sorted(spans_for_query, key=lambda x: sum([1 / (get_unigram_freq(w) + 1) - 1e-3 for w in x.split()]),
                                 reverse=True)
        logger.debug(f"Too many query spans for phonetic index, filtering out the following for efficiency: "
                     f"{spans_for_query[queries_to_keep:]}")
        spans_for_query = spans_for_query[:queries_to_keep]

    if len(spans_for_query) == 0:
        # nothing to do here!
        return span2entsim

    logger.info(f"Querying phonetic index with spans: {spans_for_query}")
    query_from_span_metaphone = lambda span: {'match': {'phonemes': {'query': doublemetaphone(span)[0], 'fuzziness': 2}}}
    query_from_span = lambda span: {'match_phrase': {'phonemes_stressless': {'query': remove_stress(span_to_phoneme_string(span)), 'slop': 10}}}
    query = {'query': {'dis_max': {'queries': [query_from_span_metaphone(span) for span in spans_for_query]}}}
    search_results = query_es_index(es, PHONE_TO_ENT_INDEX, query, size=topn, timeout=ES_QUERY_TIMEOUT)  # list of dicts

    # filter out spans that weren't part of the query
    spans = [s for s in spans if any(s in s1 for s1 in spans_for_query)]
    # precompute latticies for efficiency
    spans_latticies = [(s, span_to_lattice(s, g2p_module), [[' '.join(x) for x in doublemetaphone(s) if len(x) > 0]]) for s in spans]

    # For each retrieved anchortext
    for hit in search_results:

        # Get the anchortext and its possible entities along with their refcounts
        source = hit['_source']
        # anchortext = make_text_like_user_text(source['span'])  # remove punc in the same way as user text so that spans match anchortexts correctly. assuming the anchortexts are the same in the phonetic ES index and the articles ES index, this shouldn't be necessary because it was already applied to the anchortexts in the articles index.
        anchortext = source['span']
        candidate_entities = json.loads(source['entities'])

        # Find utt_span, the most phonetically similar span in spans, above a threshold
        anchortext_lattice = [[source['phonemes_stressless']]]
        anchortext_metaphone = [[' '.join(x) for x in doublemetaphone(anchortext) if len(x) > 0]]
        utt_span = None
        max_ratio = -1
        for span, lattice, metaphone_lattice in spans_latticies:
            ratio = get_lattice_similarity(lattice, anchortext_lattice, threshold=SIMILARITY_RATIO_THRESHOLD, ignore_stress=True)
            metaphone_ratio = get_lattice_similarity(metaphone_lattice, anchortext_metaphone, threshold=SIMILARITY_RATIO_THRESHOLD)
            ratio = metaphone_ratio * .25 + ratio * .75
            if ratio > max_ratio:
                max_ratio = ratio
                utt_span = span
        if max_ratio < SIMILARITY_RATIO_THRESHOLD:
            continue

        span2entsim[utt_span][anchortext]['similarity'] = max_ratio
        if 'entnames' not in span2entsim[utt_span][anchortext]:
            span2entsim[utt_span][anchortext]['entnames'] = set(candidate_entities)
        else:
            span2entsim[utt_span][anchortext]['entnames'].update(candidate_entities)

    # Log
    logger.debug("Got these phonetically-corrected potential entity candidates:\n{}".format('\n'.join(
        [f"'{span}' -> {entinfo}" for span, entinfo in span2entsim.items()]
    )))

    return span2entsim

if __name__ == "__main__":

    # Run this to demo

    # Setup logging
    from chirpy.core.logging_utils import setup_logger, LoggerSettings
    LOGTOSCREEN_LEVEL = logging.DEBUG
    logger_settings = LoggerSettings(logtoscreen_level=LOGTOSCREEN_LEVEL, logtoscreen_usecolor=True,
                                     logtofile_level=None, logtofile_path=None,
                                     logtoscreen_allow_multiline=True, integ_test=False, remove_root_handlers=False)
    setup_logger(logger_settings)

    from chirpy.core.asr.index_phone_to_ent import MockG2p

    mock_g2p_module = MockG2p()

    # get_asr_aware_span2entsim(['china'], mock_g2p_module)
    get_asr_aware_span2entsim(['their eyes of sky walker', 'of sky walker', 'eye of sky'], mock_g2p_module)
    # get_asr_aware_span2entsim(['four v ferrari', 'four v', 'ferrari'], mock_g2p_module)
    get_asr_aware_span2entsim(['mary puppets'], mock_g2p_module)
