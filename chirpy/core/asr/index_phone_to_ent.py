# DO NOT RUN THIS SCRIPT UNLESS YOU'RE ABSOLUTELY SURE YOU KNOW WHAT YOU'RE DOING!!
#
# This script indexes phonetic representations of anchortexts in Wikipedia.
# It takes a Spark dump (WIKI_ENTITIES) that Haojun prepares that contains mappings from anchortexts to Wikipedia
# entities, and indexes these anchortext spans into an elasticsearch index (PHONE_TO_ENT_INDEX) that maps phonetic
# representations of spans to entities.
# This script should be run when there's an significant update to the set of Wikipedia entities in our dump, or when
# the mechanism to map spans to phonetic representations changes in g2p.py.

from concurrent import futures
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
from glob import glob
from metaphone import doublemetaphone
import json
import os
import re

from chirpy.core.asr.g2p import g2p
from chirpy.core.util import get_es_host, get_elasticsearch
from chirpy.core.asr.lattice import remove_stress, lattice_to_phonemes

PHONE_TO_ENT_INDEX = "phone_doc-0520-3"
WIKI_ENTITIES = "/u/scr/nlp/data/Wikipedia/enwiki-20200520-pages-articles-multistream-spans.json.bz2"

def ensure_index(index_name):
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, ignore=400,
            body=json.dumps({
                "mappings": {"doc": {"properties": {
                    "phonemes": {"type": "text" },
                    "phonemes_stressless": {"type": "text", "analyzer": "whitespace", "index_phrases": True},
                    "span": {"type": "text"},
                    "entities": {"type": "text"},
                  }},
                }
              }))


def delete_index(index_name):
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name, ignore=[400, 403])


def span_to_phoneme_string(span: str, g2p_module = None) -> str:
    return ' '.join([x for x in g2p(span, g2p_module) if x != ' '])  # remove word boundaries


def index(bz2file, idx):
    id = 0
    queries = []
    with futures.ThreadPoolExecutor(16) as executor:
        with bz2.open(bz2file) as f:
            for line in tqdm(f, position=idx % 12 + 1, desc=f"File {idx}", leave=False):
            # for line in f:
                obj = eval(line.decode('utf-8').rstrip())
                if obj[0].startswith(':') or obj[0].startswith('thumb|') or len(obj[0].split()) > 10 or "</" in obj[0]\
                        or obj[0].startswith('category:'):
                    id += 1
                    continue

                span = re.sub(" \(.*\)$", "", obj[0])

                phoneme_string = span_to_phoneme_string(span, g2p_module)
                phoneme_string_stressless = remove_stress(phoneme_string)

                metaphone_strings = set(filter(lambda x: len(x) > 0, doublemetaphone(span)))
                # further augmentation
                augment_pairs = {"X": ["K"], "K": ["X"]}
                augmented_metaphone_strings = set()
                for x in metaphone_strings:
                    lattice = []
                    for y in x:
                        if y in augment_pairs:
                            lattice.append([y] + augment_pairs[y])
                        else:
                            lattice.append([y])
                    augmented_metaphone_strings.update(lattice_to_phonemes(lattice))

                item = {
                    'span': obj[0],
                    'phonemes': [x.replace(' ', '') for x in augmented_metaphone_strings],
                    'phonemes_stressless': phoneme_string_stressless,
                    'entities': json.dumps([x for x in obj[1] if not x.startswith('Category:') and not x.startswith(':')])
                }
                query = "{}\n{}".format(json.dumps({ 'index': { '_id': f'span-{os.path.basename(bz2file)}-{id}' } }), json.dumps(item))
                queries.append(query)
                id += 1

                if len(queries) >= 2000:
                    executor.submit(es.bulk, index=PHONE_TO_ENT_INDEX, doc_type='doc', body='\n'.join(queries), timeout='100s')
                    queries = []

        if len(queries) > 0:
            executor.submit(es.bulk, index=PHONE_TO_ENT_INDEX, doc_type='doc', body='\n'.join(queries), timeout='100s')

        executor.shutdown(wait=True)

class MockG2p:
    def __init__(self):
        from g2p_en import G2p
        self.g2p = G2p()

    def safe_execute(self, text):
        return self.g2p(text)

if __name__ == "__main__":
    # DO NOT RUN THIS SCRIPT UNLESS YOU'RE ABSOLUTELY SURE YOU KNOW WHAT YOU'RE DOING!!

    # comment out this line to actually run indexing
    exit()

    import bz2
    from tqdm import tqdm
    from multiprocessing import Pool

    g2p_module = MockG2p()

    es = get_elasticsearch()
    
    delete_index(PHONE_TO_ENT_INDEX)
    ensure_index(PHONE_TO_ENT_INDEX)

    pool = Pool()
    pbar = tqdm(total=len(glob(os.path.join(WIKI_ENTITIES, '*.bz2'))))

    for i, fn in enumerate(glob(os.path.join(WIKI_ENTITIES, '*.bz2'))):
        pool.apply_async(index, [fn, i], callback=lambda x: pbar.update(), error_callback=print)
        # index(fn, i); pbar.update()

    pool.close()
    pool.join()