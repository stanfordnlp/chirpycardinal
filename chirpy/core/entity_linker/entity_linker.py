import logging
from concurrent import futures
from typing import List, Dict, Optional, Set

from chirpy.annotators.g2p import NeuralGraphemeToPhoneme
from chirpy.core.asr.search_phone_to_ent import get_asr_aware_span2entsim
from chirpy.core.callables import Annotator
from chirpy.core.entity_linker.entity_linker_classes import LinkedSpan, EntityLinkerResult, WikiEntity
from chirpy.core.entity_linker.util import add_all_alternative_spans
from chirpy.core.entity_linker.resolve_conflicts import comparison_fn_nested_spans, comparison_fn_alternative_spans, \
    resolve_pairwise_conflicts
from chirpy.core.entity_linker.thresholds import SCORE_THRESHOLD_HIGHPREC, UNIGRAM_FREQ_THRESHOLD
from chirpy.core.entity_linker.entity_groups import EntityGroup, ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.entity_linker.wiki_data_fetching import get_entities_by_anchortext, get_entities_by_wiki_name
from chirpy.core.entity_linker.lists import LOW_PREC_SPANS, MANUAL_SPAN2ENTINFO, DONT_LINK_WORDS, get_unigram_freq
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.core.regex.templates import MyNameIsTemplate
from chirpy.annotators.navigational_intent.navigational_intent import NavigationalIntentOutput
from chirpy.core.state_manager import StateManager
from chirpy.core.util import remove_punc, get_ngrams, filter_and_log, make_text_like_user_text
from chirpy.core.latency import measure
from chirpy.core.flags import USE_ASR_ROBUSTNESS_OVERALL_FLAG

# from functools import lru_cache  # uncomment for eval
# from entity_linker_eval.eval.util import transform_args_for_cache  # uncomment for eval

logger = logging.getLogger('chirpylogger')

# If we supply corenlp input, these are the only NER types we will make sure to link
# See https://stanfordnlp.github.io/CoreNLP/ner.html
HIGH_PRIORITY_NER_TYPES = ['PERSON', 'LOCATION', 'ORGANIZATION', 'MISC', 'CITY', 'STATE_OR_PROVINCE', 'COUNTRY',
                           'NATIONALITY', 'RELIGION', 'TITLE', 'IDEOLOGY']

# We attempt to link all ngrams inside the user utterance, up to this maximum
MAX_NGRAM_TO_LINK = 5

def is_dont_link_word(word: str) -> bool:
    """
    Returns True iff:
        - word is in DONT_LINK_WORDS, or
        - word has an apostrophe with the first part in DONT_LINK_WORDS (e.g. word = "what's"), or
        - word is all digits
    """
    assert " " not in word
    if word in DONT_LINK_WORDS:
        return True
    if "'" in word:
        parts = word.split("'")
        if len(parts) == 2 and len(parts[1]) <= 2 and parts[0] in DONT_LINK_WORDS:
            return True
    if all(c in '1234567890' for c in word):
        return True
    return False


def should_link(span: str, include_common_phrases: bool) -> bool:
    """
    Determines whether we should attempt to link a span to entities.

    If include_common_phrases is False, spans consisting entirely of DONT_LINK_WORDS are not linked.
    If include_common_phrases is True, multi-word (ngrams with n>1) spans consisting entirely of DONT_LINK_WORDS are
        linked. Spans which are a single DONT_LINK_WORD are still not linked.
    """
    if span in MANUAL_SPAN2ENTINFO:
        return True

    elif contains_offensive(span, 'Span "{}" contains offensive phrase "{}" so will not try to entity link'):
        return False

    # If span consists entirely of DONT_LINK_WORDS, only include if it's multi-word and include_common_phrases=True
    elif all(is_dont_link_word(word) for word in span.split()):
        if len(span.split()) > 1 and include_common_phrases:
            return True
        else:
            logger.debug(f'Not linking span "{span}" because it consists of DONT_LINK_WORDS')
            return False

    else:
        return True


def is_high_prec(linked_span: LinkedSpan, score_threshold: int, unigram_freq_threshold: int, expected_type: Optional[EntityGroup]) -> bool:
    """
    Returns whether this LinkedSpan should be put in the high precision set or not.
    """

    # If it's a manual link with force_high_prec, it's high prec
    if linked_span.manual_top_ent and linked_span.manual_top_ent_force_highprec:
        return True

    # Anything on the LOW_PREC_SPANS list is low prec
    if linked_span.span in LOW_PREC_SPANS:
        return False

    # Anything with a score below the threshold is low prec
    if linked_span.top_ent_score < score_threshold:
        return False

    # If it's of expected_type and has score above the threshold, it's high prec
    if expected_type and expected_type.matches(linked_span.top_ent) and linked_span.top_ent_score >= score_threshold:
        logger.info(f'LinkedSpan {linked_span} is high-precision because the top_ent is of expected type and its score is above {score_threshold}')
        return True

    # If the rarest unigram in the span has frequency above the threshold, it's low prec
    if linked_span.min_unigram_freq > unigram_freq_threshold:
        return False

    # Otherwise, high precision
    return True


def sort_linked_spans(linked_spans: Set[LinkedSpan]) -> List[LinkedSpan]:
    """Sort the linked spans by priority"""
    return sorted(list(linked_spans), key=lambda ls: (
        ls.protection_level,  # sort by protection level
        ls.top_ent_score,  # then sort by score
    ), reverse=True)


def get_asr_robust_entities(spans: Set[str], g2p_module=None):
    try:
        # Fetch ASR-robust entity info
        asr_entity_info = get_asr_aware_span2entsim(spans, g2p_module)
    except:
        asr_entity_info = dict()

    # Add entity candidates from ASR
    if len(asr_entity_info) > 0:
        asr_entities = ['"{}" -> "{}"'.format(span, ent_name)
                        for span, anc2info in asr_entity_info.items()
                        for anchortext, info in anc2info.items()
                        for ent_name in info.get('entnames', [])]
        print_limit = 10
        logger.info('Getting the entities from ASR-correction:\n{}'.format(
            '\n'.join(asr_entities[:print_limit])
            + ("" if len(
                asr_entities) <= print_limit else f"\n... and {len(asr_entities) - print_limit} more ...")))
        asr_ent_names = [ent_name for span, anc2info in asr_entity_info.items()
                         for anchortext, info in anc2info.items()
                         for ent_name in info.get('entnames', [])]
        asr_entname2ent = get_entities_by_wiki_name(asr_ent_names)
    else:
        asr_entname2ent = dict()

    return asr_entname2ent, asr_entity_info

@measure
# @transform_args_for_cache  # uncomment for faster eval
# @lru_cache(maxsize=128)  # uncomment for faster eval
def link_spans(spans: Set[str], use_asr_robustness: bool, altspan2origspan: Dict[str, str] = {}, proper_nouns: List[str] = [],
               ner_span2type: Dict[str, str] = {}, g2p_module = None, expected_type: Optional[EntityGroup] = None) -> Set[LinkedSpan]:
    """
    Input:
        spans: The spans we want to try to link to entities.
        altspan2origspan: Dict mapping from any alternative span in spans (which we will use to search) to its
            original span (the span as it appears in the original text).
        proper_nouns: List of proper nouns. LinkedSpans whose span is in proper_nouns will be marked as such.
        ner_span2type: Dict mapping from span to NER type (str). LinkedSpans whose span is a named entity will be marked
            with their NER type.
        g2p_module: remote module for grapheme to phoneme
        expected_type: EntityGroup representing the type of entities we expect the user to mention, or None.
        use_asr_robustness: If True, use ASR robustness in the entity linker (i.e. additionally consider phonetically
            similar entities). This makes the function significantly slower, so only include if spans might contain
            ASR errors. USE_ASR_ROBUSTNESS_OVERALL_FLAG also needs to be True for ASR robustness to be on.

    Returns:
        linked_spans: Set of LinkedSpans. Might be fewer than spans.
    """
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        if USE_ASR_ROBUSTNESS_OVERALL_FLAG and use_asr_robustness:
            # Fetch ASR-robust entity info
            asr_robust_result = executor.submit(get_asr_robust_entities, set([altspan2origspan.get(s, s) for s in spans]), g2p_module)
        else:
            asr_robust_result = None

        # Fetch WikiEntities
        entities = executor.submit(get_entities_by_anchortext, spans)

    asr_entname2ent, asr_entity_info = asr_robust_result.result() if asr_robust_result is not None else (dict(), dict())
    entities = entities.result()

    entity_names_to_entities = {e.name: e for e in entities}
    entity_names_to_entities.update(asr_entname2ent)

    # Create the list of LinkedSpans
    linked_spans = set()
    for span in spans:

        # Get the set of candidate entities which have span among their anchortexts
        candidate_entities = {e for e in entities if span in e.anchortext_counts.keys()}

        # If there are no such candidate entities, and we have no phonetically-related anchortexts for this span, continue
        if not candidate_entities and span not in asr_entity_info:
            continue

        # Make a dict mapping from anchortext (str) to sim(anchortext, span)
        asr_span_similarities = {anchortext: anc2info['similarity'] for anchortext, anc2info in asr_entity_info.get(span, {}).items()
                                                 if any(e in entity_names_to_entities for e in anc2info.get('entnames', []))}
        asr_span_similarities[span] = 1
        if span in asr_entity_info:

            # Add any entities which we got from the phonetic index
            for anchortext, info in asr_entity_info[span].items():
                for e in info.get('entnames', []):
                    if e in entity_names_to_entities:
                        if anchortext not in entity_names_to_entities[e].anchortext_counts:
                            logger.error(f'anchortext "{anchortext}" is not in anchortext_counts for entity {entity_names_to_entities[e]}, but '
                                         f'according to the phonetic ES index it is. This is likely due to a discrepancy'
                                         f'between the phonetic ES index and the articles ES index. Removing entity {entity_names_to_entities[e]}'
                                         f'from the candidates for span "{span}".')
                            continue
                        else:
                            candidate_entities.add(entity_names_to_entities[e])

            if len(candidate_entities) == 0:
                continue

        orig_span = altspan2origspan[span] if span in altspan2origspan else span
        unigram_freqs = [get_unigram_freq(unigram) for unigram in orig_span.split()]  # freq of the unigrams in span
        min_unigram_freq = min(unigram_freqs)  # freq of the rarest word. int.
        linked_span = LinkedSpan(span=orig_span,
                                 candidate_entities=candidate_entities,
                                 min_unigram_freq=min_unigram_freq,
                                 span_used_for_search=span,
                                 ner_type=ner_span2type[orig_span] if orig_span in ner_span2type else None,
                                 is_proper_noun=orig_span in proper_nouns,
                                 span_similarities=asr_span_similarities,
                                 expected_type=expected_type)

        # Check if the LinkedSpan has no entities (after internal filtering)
        if linked_span.is_empty:
            logger.info(f'LinkedSpan for span="{linked_span.span}" is empty, after filtering out entities. Discarding.')
        else:
            linked_spans.add(linked_span)

    return linked_spans

@measure
def entity_link(user_utterance: str, corenlp: Optional[dict] = None, g2p_module = None,
                max_ngram: int = MAX_NGRAM_TO_LINK, include_common_phrases: bool = False,
                expected_type: Optional[EntityGroup] = None) -> EntityLinkerResult:
    """
    The top-level entity-linking function. Tries to link all possible spans in user_utterance to entities, and returns
    an EntityLinkerResult.

    Input:
        user_utterance: string. the current user utterance we want to entity link.
        corenlp: If provided, the output of the corenlp module that runs in the NLP pipeline.
            In particular, contains 'proper_nouns' -> list of strings, 'ner_mentions' -> list of (string, string) pairs.
        g2p_module: remote module for grapheme to phoneme
        max_ngram: we only attempt to link spans up to this length, plus proper_nouns and ner_mentions as identified
            by corenlp.
        expected_type: If supplied, an EntityGroup which defines a group of entities we expect the user to mention
            on this turn.

    Output:
        an EntityLinkerResult
    """
    assert expected_type is None or isinstance(expected_type, EntityGroup), f"expected_type should be None or EntityGroup, not {type(expected_type)}"

    # Lowercase and remove punctuation from user_utterance, keeping apostrophes
    user_utterance = make_text_like_user_text(user_utterance)

    if not user_utterance:
        return EntityLinkerResult()

    if corenlp is None:
        corenlp = {'proper_nouns': [], 'ner_mentions': [], 'nounphrases': [], 'tokens': []}

    logger.primary_info(f'Entity linker starting with user_utterance="{user_utterance}" and include_common_phrases={include_common_phrases}')

    # Get proper_nouns, nounphrases and named entities from corenlp, removing unwanted NER types
    nounphrases = corenlp['nounphrases']
    proper_nouns = corenlp['proper_nouns']
    ner_mentions = corenlp['ner_mentions']
    corenlp_tokens = corenlp['tokens']
    ner_mentions = [(span, type_str) for (span, type_str) in ner_mentions if type_str in HIGH_PRIORITY_NER_TYPES]
    ner_span2type = {span: type for span, type in ner_mentions}

    # Get all ngrams (up to max_ngram) in user_utterance
    ngrams = set()
    for n in range(1, min(len(user_utterance.strip().split()), max_ngram) + 1):
        ngrams.update(get_ngrams(user_utterance, n))

    spans_to_lookup = ngrams  # set

    # Make sure that all proper nouns, nounphrases and NER mentions will be looked up
    spans_to_lookup.update(set(proper_nouns))
    spans_to_lookup.update(set(nounphrases))
    spans_to_lookup.update(set(ner_span2type.keys()))

    # Remove any spans that should be eliminated
    spans_to_lookup = {span for span in spans_to_lookup if should_link(span, include_common_phrases)}

    # Add alternative forms of spans to spans_to_lookup
    spans_to_lookup, altspan2origspan = add_all_alternative_spans(spans_to_lookup, ngrams, corenlp_tokens)

    # Remove any spans that should be eliminated, again
    spans_to_lookup = {span for span in spans_to_lookup if should_link(span, include_common_phrases)}

    # Run linker on all spans_to_lookup
    linked_spans = link_spans(spans_to_lookup, True, altspan2origspan, proper_nouns, ner_span2type, g2p_module, expected_type)

    # Log
    logger.info('Got these LinkedSpans (sorted by score):\n{}'.format('\n'.join([repr(ls) for ls in sort_linked_spans(linked_spans)])))

    # Start with all spans as high_prec
    high_prec = linked_spans
    conflict_removed = set()  # LinkedSpans that were removed from high prec set due to a conflict with another LinkedSpan
    threshold_removed = set()  # LinkedSpans that were removed from high prec set due to score/unigram thresholds

    # Within the high precision set, if there are multiple versions of one span, choose the best one, and remove the others
    def comparison_fn_alternative_spans_withtype(linkedspan1: LinkedSpan, linkedspan2: LinkedSpan):
        return comparison_fn_alternative_spans(linkedspan1, linkedspan2, expected_type)
    high_prec, removed_linkedspans = resolve_pairwise_conflicts(high_prec, comparison_fn_alternative_spans_withtype)
    conflict_removed.update(removed_linkedspans)

    # Within the high precision set, if there are nested spans, choose the largest one, and remove the others
    def comparison_fn_nested_spans_withtype(linkedspan1: LinkedSpan, linkedspan2: LinkedSpan):
        return comparison_fn_nested_spans(linkedspan1, linkedspan2, expected_type)
    high_prec, removed_linkedspans = resolve_pairwise_conflicts(high_prec, comparison_fn_nested_spans_withtype)
    conflict_removed.update(removed_linkedspans)

    # Within the high precision set, remove any which have too low score / too high unigram freq
    for ls in list(high_prec):
        if not is_high_prec(ls, SCORE_THRESHOLD_HIGHPREC, UNIGRAM_FREQ_THRESHOLD, expected_type):
            logger.info(f'Moving {ls} from high_prec to low_prec set based on unigram_freq / score')
            high_prec.remove(ls)
            threshold_removed.add(ls)

    # Sort each set by priority
    high_prec = sort_linked_spans(high_prec)  # list
    threshold_removed = sort_linked_spans(threshold_removed)  # list
    conflict_removed = sort_linked_spans(conflict_removed)  # list

    # Log
    logger.info('Got {} high-precision linked spans (highest priority first):\n\n{}'.format(
        len(high_prec), '\n\n'.join([linked_span.detail_repr for linked_span in high_prec])
    ))
    logger.info('Got {} threshold-removed (low prec) linked spans (highest priority first):\n\n{}'.format(
        len(threshold_removed), '\n\n'.join([linked_span.detail_repr for linked_span in threshold_removed])
    ))
    logger.info('Got {} conflict-removed (low prec) linked spans (highest priority first):\n\n{}'.format(
        len(conflict_removed), '\n\n'.join([linked_span.detail_repr for linked_span in conflict_removed])
    ))

    # Return results
    result = EntityLinkerResult(high_prec, threshold_removed, conflict_removed)
    logger.primary_info(f'Final output of entity linker for user utterance "{user_utterance}":\n{result}')
    return result



class EntityLinkerModule(Annotator):
    name='entity_linker'
    def __init__(self, state_manager: StateManager, timeout=3, input_annotations = ('navigational_intent',)):
        super().__init__(state_manager=state_manager, timeout=timeout,  input_annotations=input_annotations,
                          url='local')
    def get_default_response(self):
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        return EntityLinkerResult()

    def should_run_entity_linker(self, user_utterance: str, history: List[str], nav_intent_output: NavigationalIntentOutput) -> bool:
        """
        Determines whether we should run the entity linker on this turn.
        """
        # If user is giving navigational intent, run entity linker
        if nav_intent_output.pos_topic_is_supplied or nav_intent_output.neg_topic_is_supplied:
            return True

        # If we just asked user their name, don't run entity linker
        if len(history) >= 1 and 'your name' in history[-1].lower():
            logger.primary_info(f'Not running entity linker on "{user_utterance}" because we just asked for user\'s name')
            return False

        # If the user is giving their name, don't run entity linker
        mynameis_slots = MyNameIsTemplate().execute(user_utterance)
        if mynameis_slots is not None and 'my_name_is_high_prec' in mynameis_slots:
            logger.primary_info(f'Not running entity linker on "{user_utterance}" because user utterance matches MyNameIs template')
            return False

        # Otherwise run entity linker
        return True

    def execute(self):
        """
        Run the entity linker on the user utterance and return EntityLinkerResult.
        """
        try:
            # Get things from state
            user_utterance = self.state_manager.current_state.text
            history = self.state_manager.current_state.history
            nav_intent_output = self.state_manager.current_state.navigational_intent
            try:
                expected_type = self.state_manager.current_state.entity_tracker.expected_type
            except:
                logger.error('Failed to get expected_type from entity_tracker so setting to None', exc_info=True)
                expected_type = None
            # corenlp = self.state_manager.current_state.corenlp  # To condition on corenlp, make sure corenlp is in module_requirements in baseline_bot.py
            corenlp = None
            g2p_module = NeuralGraphemeToPhoneme(self.state_manager)

            # Determine if we should run entity linker on this turn, and run
            if self.should_run_entity_linker(user_utterance, history, nav_intent_output):
                return entity_link(user_utterance, corenlp, g2p_module, include_common_phrases=(expected_type is not None))
            else:
                return self.get_default_response()
        except Exception:
            logger.error('Encountered an error when running entity linker. Returning empty results.', exc_info=True)
            return self.get_default_response()



if __name__ == "__main__":
    # You can test the entity linker by running this code

    from chirpy.core.latency import save_latency_plot

    # Setup logging with interactive mode logger settings
    from chirpy.core.logging_utils import setup_logger, LoggerSettings
    LOGTOSCREEN_LEVEL = logging.DEBUG
    logger_settings = LoggerSettings(logtoscreen_level=LOGTOSCREEN_LEVEL, logtoscreen_usecolor=True,
                                     logtofile_level=None, logtofile_path=None,
                                     logtoscreen_allow_multiline=True, integ_test=False, remove_root_handlers=False)
    setup_logger(logger_settings)

    # # Init corenlp module
    # import requests
    # class TestModule:
    #     def __init__(self, url):
    #         self.url = url
    #     def execute(self, data):
    #         response = requests.post(self.url, data=json.dumps(data), headers={'content-type': 'application/json'}, timeout=10)
    #         return response

    # Define input
    user_utterance = "sweatpants"
    expected_type = ENTITY_GROUPS_FOR_EXPECTED_TYPE.clothing_related

    # # Get corenlp
    # from chirpy.annotators.corenlp import get_nounphrases, get_propernouns, get_ner, get_simple_sentiment
    # corenlp_output = corenlp_module.execute({'text': user_utterance, 'annotators': 'pos,ner,parse,sentiment'}).json()
    # corenlp = {
    #     'nounphrases': get_nounphrases(corenlp_output),
    #     'proper_nouns': get_propernouns(corenlp_output),
    #     'ner_mentions': get_ner(corenlp_output),
    #     'sentiment': get_simple_sentiment(corenlp_output),
    # }
    corenlp = None

    from chirpy.core.asr.index_phone_to_ent import MockG2p

    mock_g2p_module = MockG2p()

    entity_link(user_utterance, corenlp, mock_g2p_module, include_common_phrases=(expected_type is not None), expected_type=expected_type)
    print('saving latency plot...')
    save_latency_plot('entity_linker_latency.png')
    print('done')