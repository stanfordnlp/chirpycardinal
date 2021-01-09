import logging
from enum import Enum
from typing import Dict, List, Optional
from nltk.tree import Tree
from nltk.treeprettyprinter import TreePrettyPrinter

from chirpy.core.callables import Annotator
from chirpy.core.state_manager import StateManager
from chirpy.core.util import catch_errors

logger = logging.getLogger('chirpylogger')

# The constituency tags we want to extract
# http://www.surdeanu.info/mihai/teaching/ista555-fall13/readings/PennTreebankConstituents.html
CONSTITUENCY_SETTINGS = {
    'nounphrases': {'tags': ['NP']},
    'verbphrases': {'tags': ['VP']},
    # 'wh_nounphrases': {'tags': ['WHNP']},
    # 'wh_adverbphrases': {'tags': ['WHADVP']},
    # 'wh_prepositionalphrases': {'tags': ['WHPP']},
}

# The POS tags we want to extract
# http://www.surdeanu.info/mihai/teaching/ista555-fall13/readings/PennTreebankConstituents.html
POS_SETTINGS = {
    'nouns': {'tags': ['NN', 'NNS'], 'merge_adjacent': False},
    'proper_nouns': {'tags': ['NNP', 'NNPS'], 'merge_adjacent': True},
}

class Sentiment(int, Enum):
    STRONG_NEGATIVE = 0
    NEGATIVE = 1
    NEUTRAL = 2
    POSITIVE = 3
    STRONG_POSITIVE = 4


@catch_errors([])
def get_constituencies_from_tree(tree: Tree, tags: List[str]):
    """
    This is a recursive function that searches through the tree (a nltk.tree.Tree) representing a constituency parse,
    and finds all nodes with a tag in tags.

    Returns:
        spans: list of strings. Each string corresponds to a node with one of the desired tags. The string is the
        node's leaves, joined together.
    """
    spans = []
    if tree.label() in tags:
        spans.append(' '.join(tree.leaves()))
    nonleaf_children = [child for child in tree if isinstance(child, Tree)]
    spans += [span for child in nonleaf_children for span in get_constituencies_from_tree(child, tags)]
    return spans


@catch_errors({tag_name: [] for tag_name in CONSTITUENCY_SETTINGS.keys()})
def get_constituencies(corenlp_output) -> Dict[str, List[str]]:
    """
    Gets all the constituencies for the tags in CONSTITUENCY_SETTINGS. See here for constituency parse tags:
    http://www.surdeanu.info/mihai/teaching/ista555-fall13/readings/PennTreebankConstituents.html

    @param corenlp_output: output of the corenlp remote module, assuming 'parse' was one of the requested annotators.
    @return: output: dict mapping from tag name (a str in CONSTITUENCY_SETTINGS.keys()) to a list of strings (the spans
        with that tag)
    """
    output = {tag_name: [] for tag_name in CONSTITUENCY_SETTINGS.keys()}
    if corenlp_output is None:
        return output

    for sentence in corenlp_output['sentences']:
        tree = Tree.fromstring(sentence['parse'])
        logger.info(f'Extracting tags ({CONSTITUENCY_SETTINGS}) from this corenlp constituency parse:\n{str(TreePrettyPrinter(tree))}')
        for tag_name, settings in CONSTITUENCY_SETTINGS.items():
            tag_phrases = get_constituencies_from_tree(tree, tags=settings['tags'])
            logger.info(f'For these tags: {settings["tags"]}, got these tag phrases: {tag_phrases}')
            output[tag_name] += get_constituencies_from_tree(tree, tags=settings['tags'])
    return output


@catch_errors([])
def get_pos_spans(corenlp_output, tags: List[str], merge_adjacent: bool) -> List[str]:
    """
    @param corenlp_output: output of the corenlp remote module, assuming 'pos' was one of the requested annotators.
    @return: output: list of strings. If merge_adjacent=False, these are words with desired tags. If
        merge_adjacent=False, these are spans whose words all have desired tags.
    """
    if corenlp_output is None:
        return []

    output = []
    logger.info('Extracting words with tags={} (merge_adjacent={}) using these corenlp pos tags:\n{}'.format(tags, merge_adjacent,
        '\n'.join(['{} ({})'.format(token['originalText'], token['pos'])
                   for sentence in corenlp_output['sentences'] for token in sentence['tokens']])))

    for sentence in corenlp_output['sentences']:
        cur_span = []  # list of tokens making up the current span
        for token in sentence['tokens']:
            if token['pos'] in tags:
                cur_span.append(token['originalText'])  # add to cur_span
            else:
                if cur_span:  # otherwise flush
                    output.append(' '.join(cur_span))
                    cur_span = []
            if cur_span and not merge_adjacent:  # if merge_adjacent=False, always flush every word
                output.append(' '.join(cur_span))
                cur_span = []
        if cur_span:
            output.append(' '.join(cur_span))
    logger.info(f'For tags={tags} and merge_adjacent={merge_adjacent}, got these spans: {output}')
    return output


@catch_errors({tag_name: [] for tag_name in POS_SETTINGS.keys()})
def get_all_pos_spans(corenlp_output) -> Dict[str, List[str]]:
    """
    Gets all the spans for the tags in POS_SETTINGS. See here for constituency parse tags:
    http://www.surdeanu.info/mihai/teaching/ista555-fall13/readings/PennTreebankConstituents.html

    @param corenlp_output: output of the corenlp remote module, assuming 'parse' was one of the requested annotators.
    @return: output: dict mapping from tag name (a str in POS_SETTINGS.keys()) to a list of strings (the spans with
        that tag)
    """
    output = {tag_name: [] for tag_name in POS_SETTINGS.keys()}
    if corenlp_output is None:
        return output

    for tag_name, settings in POS_SETTINGS.items():
        output[tag_name] = get_pos_spans(corenlp_output, tags=settings['tags'], merge_adjacent=settings['merge_adjacent'])
    return output


@catch_errors([])
def get_tokens(corenlp_output) -> List[dict]:
    """
    @param corenlp_output: output of the corenlp remote module, assuming 'pos' was one of the requested annotators.
    @return: A list of dicts. Each dict corresponds to one token and contains the keys 'originalText', 'lemma' and 'pos'.
    """
    tokens = [token for sentence in corenlp_output['sentences'] for token in sentence['tokens']]
    tokens = [{k: v for k, v in token.items() if k in ['originalText', 'lemma', 'pos']} for token in tokens]
    return tokens


@catch_errors([])
def get_ner(corenlp_output, filter_pronouns=True):
    """
    @param corenlp_output: output of the corenlp remote module, assuming 'ner' was one of the requested annotators.
    @param filter_pronouns: if True, we will filter out NER mentions that are pronouns
    @return: ner_mentions: list of (span, type) pairs where span is a string (e.g. 'elizabeth warren') and type is a
        string (e.g. 'PERSON'). List of types here: https://stanfordnlp.github.io/CoreNLP/ner.html
    """
    if corenlp_output is None:
        return []

    ner_mentions = []
    if not any('entitymentions' in sentence for sentence in corenlp_output['sentences']):
        logger.info('No entity mentions, probably because we did not run corenlp with ner annotator')
        return []
    logger.info('Getting NER mentions (with filter_pronouns={}) from these corenlp entitymentions: {}'.format(
        filter_pronouns, [sentence['entitymentions'] for sentence in corenlp_output['sentences']]))
    for sentence in corenlp_output['sentences']:
        for mention in sentence['entitymentions']:
            span, type = mention['text'], mention['ner']

            # Filter out mentions that are all pronoun
            if filter_pronouns:

                # Get the pos tags of the words in this mention
                start, end = mention['tokenBegin'], mention['tokenEnd']
                tokens = sentence['tokens'][start: end]
                pos_tags = [token['pos'] for token in tokens]

                # http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.9.8216&rep=rep1&type=pdf
                # https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
                if all([pos_tag in ['PRP', 'PP$', 'PRP$', 'WP', 'WP$'] for pos_tag in pos_tags]):
                    continue

            ner_mentions.append((span, type))
    logger.info(f'Got these NER mentions: {ner_mentions}')
    return ner_mentions


@catch_errors([])
def get_detailed_sentiment(corenlp_output):
    """
    @param corenlp_output: output of the corenlp remote module, assuming 'sentiment' was one of the requested annotators
    @return: sentiment_info: list of dictionaries, each one corresponding to a sentence in the input text.
    """
    if corenlp_output is None:
        return []

    sentiment_info = [
        {'text': ' '.join([token['originalText'] for token in sentence['tokens']]),  # str
         'sentiment': Sentiment(int(sentence['sentimentValue'])),  # Sentiment type
         'sentiment_dist': sentence['sentimentDistribution'],  # list length 5, sums to 1
         'sentiment_tree': sentence['sentimentTree'],  # str
        } for sentence in corenlp_output['sentences']]
    return sentiment_info


@catch_errors(Sentiment.NEUTRAL)
def get_simple_sentiment(corenlp_output):
    """
    This function assumes that corenlp was run on the user utterance, which is one "sentence" because we don't have
    punctuation. It returns a single sentiment label for the user utterance.

    @param corenlp_output: output of the corenlp remote module, assuming 'sentiment' was one of the requested annotators
    @return: sentiment: a Sentiment
    """
    if corenlp_output is None:
        logger.warning('Due to absence of corenlp output, marking sentiment as NEUTRAL')
        return Sentiment.NEUTRAL

    if len(corenlp_output['sentences']) == 0:
        logger.warning("corenlp_output['sentences'] has length 0 so returning sentiment=2 (neutral)")
        return Sentiment.NEUTRAL

    if len(corenlp_output['sentences']) > 1:
        logger.warning(f"corenlp_output['sentences'] has length {len(corenlp_output['sentences'])}>1 so returning sentiment for the first sentence only")

    sentence = corenlp_output['sentences'][0]
    return Sentiment(int(sentence['sentimentValue']))


@catch_errors([])
def get_sentences(corenlp_output):
    """
    Returns:
        sentences: List of strings - each a sentence as it appears in the original text.
    """
    if corenlp_output is None:
        return []

    sentences_to_return = []
    for corenlp_sent in corenlp_output['sentences']:
        tokens = corenlp_sent['tokens']
        sent_str = ''
        for t in tokens:
            sent_str += t['originalText'] + t['after']
        sentences_to_return.append(sent_str.strip())

    return sentences_to_return


class CorenlpModule(Annotator):
    name='corenlp'
    def __init__(self, state_manager: StateManager, timeout=5.0, url=None, input_annotations = []):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url, input_annotations=input_annotations)

    def get_input_text(self) -> Optional[str]:
        """Gets user utterance"""
        return self.state_manager.current_state.text

    def get_default_response(self):
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        output = {
            'ner_mentions': [],
            'sentiment': Sentiment.NEUTRAL,
        }
        for tag_name in list(CONSTITUENCY_SETTINGS.keys()) + list(POS_SETTINGS.keys()):
            output[tag_name] = []
        return output

    def execute(self, input_data: dict = None):
        """
        If input_data is not None, run CoreNLP on input_data. Otherwise, run on user utterance.

        @return: a dict with the keys:
            'ner_mentions' -> list of (string, string) pairs
            'sentiment' -> Sentiment
            'tokens' -> list of dictionaries, each corresponding to a token
            'nounphrases' -> list of strings
            'verbphrases' -> list of strings
            'proper_nouns' -> list of strings
            'nouns' -> list of strings
        """
        if input_data is None:
            text = self.get_input_text()
            input_data = {'text': text, 'annotators': 'pos,ner,parse,sentiment'}
        if not input_data['text']:
            return self.get_default_response()
        corenlp_output = self.remote_call(input_data)
        if corenlp_output is None:
            default_response = self.get_default_response()
            logger.info(f'{type(self).__name__} using default response: {default_response}')
            return default_response
        output = {
            'ner_mentions': get_ner(corenlp_output),
            'sentiment': get_simple_sentiment(corenlp_output),
            'tokens': get_tokens(corenlp_output),
        }
        for tag_name, phrases in get_constituencies(corenlp_output).items():
            output[tag_name] = phrases
        for tag_name, phrases in get_all_pos_spans(corenlp_output).items():
            output[tag_name] = phrases
        return output

# Explanation: if you uncomment corenlp_bot in baseline_bot.py, this works as-is to get corenlp annotations for the last
# bot utterance in the NLP pipeline. It seems like a good idea to keep the CoreNLP_user and CoreNLP_bot modules separate
# in the NLP pipeline so we get DAG efficiency benefits.
class CorenlpBotModule(CorenlpModule):
    """This remote module is like CorenlpModule, except that it runs on the last bot utterance by default, rather
    than the user utterance."""

    def get_input_text(self) -> Optional[str]:
        """Returns the last bot utterance if it exists, otherwise None"""
        history = self.state_manager.current_state.history
        if history:
            bot_utterance = history[-1]
            return bot_utterance
        return None
