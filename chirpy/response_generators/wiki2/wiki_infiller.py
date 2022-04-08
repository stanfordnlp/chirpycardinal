import logging
from typing import List
import re
import functools

from chirpy.annotators.corenlp import Sentiment
from chirpy.annotators.infiller import Infiller
from chirpy.annotators.colbertinfiller import ColBERTInfiller
from chirpy.annotators.corenlp import CorenlpModule
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_CLASSIFICATION
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.latency import measure
from chirpy.core.util import get_ngrams
from chirpy.annotators.sentseg import NLTKSentenceSegmenter
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.core.smooth_handoffs import SmoothHandoff
import json
import os
import chirpy.response_generators.wiki2.wiki_utils as wiki_utils
from ast import literal_eval as make_tuple


ENTITY_PLACEHOLDER_NOM = '{entity}'
ENTITY_PLACEHOLDER_ACC = '{entity_acc}'
ENTITY_PLACEHOLDER_GEN = '{entity_gen}'


logger = logging.getLogger('chirpylogger')

RESPONSE_TEMPLATES_FILEPATH = os.path.join(os.path.dirname(__file__), 'response_templates.json')
SECTION_TEMPLATES_FILEPATH = os.path.join(os.path.dirname(__file__), 'section_templates.json')
HANDWRITTEN_INFILLS_FILEPATH = os.path.join(os.path.dirname(__file__), 'handwritten_infills.json')
CAT_RANKING_FILEPATH = os.path.join(os.path.dirname(__file__), 'category_ranking.txt')
CAT_ASSOC_FILEPATH = os.path.join(os.path.dirname(__file__), 'category_associations.txt')

with open(RESPONSE_TEMPLATES_FILEPATH, 'r') as f:
    response_templates = json.load(f)

with open(SECTION_TEMPLATES_FILEPATH, 'r') as f:
    section_templates = json.load(f)

with open(HANDWRITTEN_INFILLS_FILEPATH, 'r') as f2:
    handwritten_infills = json.load(f2)

# category -> ranking number
category_ranking = {}
with open(CAT_RANKING_FILEPATH, 'r') as f3:
    # file lists categories in order of rank
    line_num = 1
    for category in f3:
        category_ranking[category] = line_num
        line_num += 1

# cluster of sorted categories (tuple) -> right category
category_clusters = {}
with open(CAT_ASSOC_FILEPATH, 'r') as f4:
    for mapping in f4:
        ind = mapping.find(':')
        cluster = make_tuple(mapping[:ind])
        category = mapping[ind + 2:]
        category_clusters[cluster] = category

def get_response_templates(category):
    logger.primary_info(f"Considering category {category}")
    return response_templates.get(category, [])

def title_contains(title, terms: List[str]):
    for term in terms:
        if term in title:
            return True
    return False

def get_template_key_for_section(title):
    section_to_template_key = {
        lambda title: title_contains(title, ['history', 'background']): 'history',
        lambda title: title_contains(title, ['career']): 'career',
        lambda title: title_contains(title, ['biography']): 'biography',
        lambda title: title_contains(title, ['early years', 'early life']): 'early-life',
        lambda title: title_contains(title, ['geography']): 'geography',
        lambda title: title_contains(title, ['background', 'origins']): 'background',
        lambda title: title_contains(title, ['plot', 'synopsis']): 'plot',
        lambda title: title_contains(title, ['description']): 'description',
        lambda title: title_contains(title, ['reception']): 'reception',
        lambda title: title_contains(title, ['education']): 'education',
        lambda title: title_contains(title, ['legacy']): 'legacy',
        lambda title: title_contains(title, ['character']): 'character',
        lambda title: title_contains(title, ['name', 'etymology']): 'etymology',
        lambda title: title_contains(title, ['economy']): 'economy',
        lambda title: title_contains(title, ['location']): 'location',
        lambda title: title_contains(title, ['music video']): 'music-video',
        lambda title: title_contains(title, ['gameplay']): 'gameplay',
        lambda title: title_contains(title, ['politics']): 'politics',
        lambda title: title_contains(title, ['culture']): 'culture',
        lambda title: title_contains(title, ['tourism']): 'tourism',
        lambda title: title_contains(title, ['criticism', 'controvers']): 'criticism'
        # lambda title: True: 'general'
    }
    for section_matches, template_key in section_to_template_key.items():
        if section_matches(title):
            return template_key
    return None

def get_section_templates(section_title):
    template_key = get_template_key_for_section(section_title.lower())
    logger.primary_info(f"Wiki utils identified {template_key} as template key for section title {section_title}.")
    if template_key is None:
        return section_templates['general']
    else:
        return section_templates[template_key] + section_templates['general']

def get_general_templates():
    return response_templates['general']

def get_acknowledgement_templates():
    return response_templates['acknowledgements']

def get_handwritten_infills(entity_name : str):
    return handwritten_infills.get(entity_name, [])

def get_category_priority(category):
    return category_ranking[category]

def get_category_from_cluster(cluster):
    # cluster must be a tuple
    if cluster not in category_clusters:
        return None
    else:
        return category_clusters[cluster]

def get_templates(cur_entity):
    """
    Fetch relevant templates for entity
    :param cur_entity:
    :return:
    """
    specific_responses = []
    best_ent_group = None
    for ent_group_name, ent_group in ENTITY_GROUPS_FOR_CLASSIFICATION.ordered_items:
        if ent_group.matches(cur_entity):
            response_templates = get_response_templates(ent_group_name)
            logger.primary_info(f"Got templates for {ent_group_name}: {response_templates}")
            specific_responses += response_templates
            if not best_ent_group: best_ent_group = ent_group_name

    if len(specific_responses) == 0:
        logging.warning(f"Couldn't find any specific templates for entity {cur_entity}.")
        return None, None
    return specific_responses, best_ent_group


def replace_entity_placeholder(s, pronouns, entity_name=None, omit_first=False):
    pron_nom, pron_acc, pron_gen = pronouns
    out = ""
    count = 0
    for token in s.split():
        for pl in (ENTITY_PLACEHOLDER_NOM, ENTITY_PLACEHOLDER_ACC, ENTITY_PLACEHOLDER_GEN):
            if pl in token:
                if not omit_first or count > 0:
                    if pl == ENTITY_PLACEHOLDER_NOM:
                        out += token.replace(pl, pron_nom) + ' '
                    elif pl == ENTITY_PLACEHOLDER_ACC:
                        out += token.replace(pl, pron_acc) + ' '
                    elif pl == ENTITY_PLACEHOLDER_GEN:
                        out += token.replace(pl, pron_gen) + ' '
                else:
                    out += entity_name + ' '
                count += 1
                break
        else:   # A for-else loop executes the `else` if the break did not run
            out += token + ' '
    return out


def revert_to_entity_placeholder(response, entity_name, prompt):
    # We know that every *future* instance of the entity has been correctly replaced already.
    # e.g. template = "I really like {entity} because {entity_gen} work is so [adjective]"
    # So we search for the __first__ instance of the entity name
    if entity_name not in response: return response
    curly_brace_items = [x for x in prompt.split() if x.startswith('{')]
    if len(curly_brace_items) == 0: return response
    return response.replace(entity_name, curly_brace_items[0], 1)   # Only replace once


MAX_CONSECUTIVE_INFILLS_PER_ENTITY = 3
MAX_COMPLETION_LENGTH = 50

# Using separate args instead of dict because caching doesn't work with dicts
@functools.lru_cache(maxsize=1024)
def call_infiller(tuples, sentences, max_length, contexts, prompts):
    infiller = Infiller(None)
    return infiller.execute({
        'tuples': tuples,
        'sentences': sentences,
        'max_length': max_length,
        'prompts': prompts,
        'contexts': contexts,
        'repetition_penalty': 1.0,
    })

@functools.lru_cache(maxsize=1024)
def call_colbertinfiller(tuples, sentences, max_length, contexts, prompts):
    infiller = ColBERTInfiller(None)
    return infiller.execute({
        'tuples': tuples,
        'sentences': sentences,
        'max_length': max_length,
        'prompts': prompts,
        'contexts': contexts,
        'repetition_penalty': 1.0,
    })

def filter_handwritten_responses(self, responses, entity_name, n_gram_size=2, n_past_bot_utterances=10, threshold=0.5):
    # Remove responses with high history overlap
    bot_utterances_to_consider = self.rg.state_manager.current_state.history[-n_past_bot_utterances:]
    if len(bot_utterances_to_consider):
        bot_utterance_ngrams = [set(get_ngrams(r.lower(), n_gram_size)) if set(get_ngrams(r.lower(), n_gram_size)) else {r.lower()} for r in bot_utterances_to_consider]
        responses_ngrams = [set(get_ngrams(c.lower(), n_gram_size)) if set(get_ngrams(c.lower(), n_gram_size)) else {c.lower()} for c in responses]
        responses_overlap = [max(len(cn & bn)/len(cn) for bn in bot_utterance_ngrams) for cn in responses_ngrams]

    filtered_responses = [c for c, o in zip(responses, responses_overlap) if o < threshold]
    if len(filtered_responses) == 0 and len(responses) > 0:
        # If no completions have low overlap, get completion with lowest overlap
        filtered_responses = [responses[responses_overlap.index(min(responses_overlap))]]
    return filtered_responses

def filter_responses(rg, responses, entity_name, n_gram_size=2, n_past_bot_utterances=10, threshold=0.5):
    # Remove offensive responses
    responses = [r for r in responses if not contains_offensive(r)]

    # Remove responses that are too long
    responses = [r for r in responses if len(r.split(' ')) <= MAX_COMPLETION_LENGTH]

    # Remove weird infill
    rgx = re.compile(r"\b(\w+) is a \1\b")  # "I do think noun is a noun"
    responses = [r for r in responses if rgx.search(r) is None]
    logger.primary_info(responses)

    rgx = re.compile(r"(\w+)\sand\s\1")  # "I also speak Greek and Greek and Latin."
    responses = [r for r in responses if rgx.search(r) is None]
    logger.primary_info(responses)

    rgx = re.compile(r"(\w{10,}).*\1", re.IGNORECASE)  # "Labrador retriever is similar to labrador retriever."
    responses = [r for r in responses if rgx.search(r) is None]
    logger.primary_info(responses)

    rgx = re.compile(r"(\w{4,})\s\1", re.IGNORECASE)  # "Labrador retriever is similar to labrador retriever."
    responses = [r for r in responses if rgx.search(r) is None]
    logger.primary_info(responses)

    responses = [r for r in responses if r.count(entity_name) <= 1] # reduce some of the duplication
    logger.primary_info(responses)

    bad_words = ['noun', 'adjective', 'verb', 'thing', 'george martin', '[', ']']
    responses = [r for r in responses if not any(bw in r.lower() for bw in bad_words)]


    rgx = re.compile(r"(\w{5,}).*\1", re.IGNORECASE)  # "Labrador retriever is similar to labrador retriever."
    responses = [r for r in responses if rgx.search(r) is None]

    responses = [r for r in responses if r.count(entity_name) <= 1] # reduce some of the duplication

    bad_words = ['noun', 'adjective', 'verb', 'thing']
    responses = [r for r in responses if not any(bw in r for bw in bad_words)]

    # Remove responses with high history overlap
    bot_utterances_to_consider = rg.state_manager.current_state.history[-n_past_bot_utterances:]
    if len(bot_utterances_to_consider):
        bot_utterance_ngrams = [set(get_ngrams(r.lower(), n_gram_size)) if set(get_ngrams(r.lower(), n_gram_size)) else {r.lower()} for r in bot_utterances_to_consider]
        responses_ngrams = [set(get_ngrams(c.lower(), n_gram_size)) if set(get_ngrams(c.lower(), n_gram_size)) else {c.lower()} for c in responses]
        responses_overlap = [max(len(cn & bn)/len(cn) for bn in bot_utterance_ngrams) for cn in responses_ngrams]

    filtered_responses = [c for c, o in zip(responses, responses_overlap) if o < threshold]
    if len(filtered_responses) == 0 and len(responses) > 0:
        # If no completions have low overlap, get completion with lowest overlap
        filtered_responses = [responses[responses_overlap.index(min(responses_overlap))]]

    return filtered_responses

# Do scoring of rankings

def get_scores(ranker, utterance, responses):
    data = {
        'context': [utterance],
        'responses': responses
    }
    logger.primary_info(f"Submitting {data}")
    results = ranker.execute(data)
    return results