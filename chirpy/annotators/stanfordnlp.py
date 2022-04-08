import json
import logging

from chirpy.core.callables import Annotator
from chirpy.core.state_manager import StateManager
from chirpy.core.util import catch_errors

logger = logging.getLogger('chirpylogger')

@catch_errors([])
def get_proper_nouns(stanfordnlp_output):
    """This function will take in a stanford nlp object and return the proper nouns
    enclosed. The way it does it is that it will attempt to find consecutive proper
    nouns and concatenate them with spaces in between.

    @param: stanfordnlp_output: output of stanfordnlp annotator. A dictionary similar in structure to
        stanfordnlp.Document.
    @return: entities: list of strings
    """
    if stanfordnlp_output is None:
        return []
    entities = []
    prev_is_propn = False
    for sent in stanfordnlp_output['_sentences']:
        for word in sent['_words']:
            if word['_upos'] == 'PROPN':
                if prev_is_propn:
                    entities[-1] += ' ' + word['_text']
                else:
                    entities.append(word['_text'])
            prev_is_propn = word['_upos'] == 'PROPN'
    return entities


def build_dependency_tree(words):
    """This method parses the words and returns a tree represented as a dictionary of root to branches.
    We remember the indices of the words instead of the actual words, so the tree returned will
    be a relationship of indices. Following the documentation are some unit tests.

    :param words: a list of stanfordnlp parsed words
    :type words: list of objects
    :return: a tree represented as dictionary of {root: ([branch*], [branch*])}
    :rtype: dictionary

    >>> s = nlp('today is a good day to die')
    >>> words = [word for sent in s.sentences for word in sent['_words']]
    >>> build_dependency_tree(words)
    {'5': (['1', '2', '3', '4'], ['7']), 'root': ([], ['5']), '7': (['6'], [])}
    >>> s = nlp('i want to talk about taylor swift the artist who nobody likes')
    >>> words = [word for sent in s.sentences for word in sent['_words']]
    >>> build_dependency_tree(words)
    {'2': (['1'], ['4']), 'root': ([], ['2']), '4': (['3'], ['6', '9']), '6': (['5'], []), '9': (['7', '8'], ['12']), '12': (['10', '11'], [])}
    """
    children = [(words[word['_governor'] - 1]['_index'] if word['_governor'] > 0 else 'root', \
                 (word['_index'], 'left' if word['_governor'] > int(word['_index']) else 'right')) \
                for word in words]
    dependency_tree = {}
    for parent, (child, direction) in children:
        if parent not in dependency_tree:
            dependency_tree[parent] = ([], [])
        dependency_tree[parent][0 if direction == 'left' else 1].append(child)
    return dependency_tree


def cat_sub_tree(root, tree, words):
    """This method concatenates words of a specific sub tree recursively. Since our tree representation
    is a dictionary keyed on parent nodes, the nodes without children (i.e. leaves) will not be
    present in the dictionary. That will be our base case.

    :param root: the root from which to start concatenating
    :type root: string
    :param tree: the entire tree
    :type tree: dictionary
    :param words: stanfordnlp parsed words
    :type words: list of objects
    :return: a list of stanfordnlp parsed words
    :rtype: list of objects

    >>> s = nlp('today is a good day to die')
    >>> words = [word for sent in s.sentences for word in sent['_words']]
    >>> t = build_dependency_tree(words)
    >>> sub_t = cat_sub_tree('7', t, words)
    >>> [word['_text'] for word in sub_t]
    ['to', 'die']
    >>> sub_t = cat_sub_tree('6', t, words)
    >>> [word['_text'] for word in sub_t]
    ['to']
    >>> sub_t = cat_sub_tree('5', t, words)
    >>> [word['_text'] for word in sub_t]
    ['today', 'is', 'a', 'good', 'day', 'to', 'die']
    """
    root_word = words[int(root) - 1]
    if root not in tree:
        return [root_word]
    left = (word for left_idx in tree[root][0] for word in cat_sub_tree(left_idx, tree, words))
    right = (word for right_idx in tree[root][1] for word in cat_sub_tree(right_idx, tree, words))
    return list((*left, root_word, *right))


def get_np_from(root, tree, words):
    """This method gets the noun phrases recursively from a root. It does so by first
    DFS search for a noun root, and extract the treelet from it. It then remove the first
    "case" from the noun phrases and return the string representation of it.

    Since stanfordnlp indexed their words from 1, we can retrieve the word from a list of
    words with words[int(root) - 1].

    :param root: the root from which to start searching
    :type root: string
    :param tree: the entire tree
    :type tree: dictionary
    :param words: stanfordnlp parsed words
    :type words: list of objects
    :return: a list of noun phrases
    :rtype: list of strings

    >>> s = nlp('i want to talk about amazon the company')
    >>> words = [word for sent in s.sentences for word in sent['_words']]
    >>> t = build_dependency_tree(words)
    >>> get_np_from('2', t, words)
    ['amazon', 'the company']
    """
    if words[int(root) - 1]['_upos'] in ['NOUN', 'PROPN']:  # found a noun root
        noun_phrase_words = cat_sub_tree(root, tree, words)
        while noun_phrase_words[0]['_dependency_relation'] == 'case':
            del noun_phrase_words[0]
        return [' '.join(map(lambda word: word['_text'], noun_phrase_words))]

    if root not in tree:  # root is a leaf since our tree is a dictionary of parent nodes
        if words[int(root) - 1]['_upos'] in ['NOUN', 'PROPN']:
            return [words[int(root) - 1]['_text']]
        return []
    left, right = tree[root]
    left_phrases = [phrase for left_idx in left for phrase in get_np_from(left_idx, tree, words)]
    right_phrases = [phrase for right_idx in right for phrase in get_np_from(right_idx, tree, words)]
    return [phrase.replace(" '", "'") for phrase in left_phrases + right_phrases if len(phrase) > 0]

@catch_errors([])
def get_nps(stanfordnlp_output):
    """This method gets the noun phrases from a stanfordnlp parsed object. It does so by
    parsing the dependency parsing output and select the treelets where the root of the
    treelet is a noun or proper noun. Then it concatenates all words in the subtree in order
    to form the noun phrase

    @param: stanfordnlp_output: output of stanfordnlp annotator. A dictionary similar in structure to
        stanfordnlp.Document.
    @return: nounphrases, a list of strings.

    >>> s = nlp('i want to talk about amazon the company')
    >>> get_nps(s)
    ['amazon', 'the company']
    >>> s = nlp("fisherman's friends")
    >>> get_nps(s)
    ["fisherman 's friends"]
    """
    if stanfordnlp_output is None:
        return []

    result = []
    for sentence in stanfordnlp_output['_sentences']:
        words = sentence['_words']
        if all(w['_upos'] not in ['NOUN', 'PROPN'] for w in words):
            return []
        if len(words) == 1:
            return [words[0]['_text']]
        t = build_dependency_tree(words)
        verb_root = t['root'][1][0]  # the "real" root of the tree, usually a verb
        result.append(get_np_from(verb_root, t, words))
    return [phrase for sent in result for phrase in sent]


@catch_errors([])
def get_nouns(stanfordnlp_output):
    """
    @param: stanfordnlp_output: output of stanfordnlp annotator. A dictionary similar in structure to
        stanfordnlp.Document.
    @return: nouns, a list of strings
    """
    if stanfordnlp_output is None:
        return []
    return [word['_text'] for sent in stanfordnlp_output['_sentences'] for word in sent['_words'] if word['_upos'] == 'NOUN']


class StanfordnlpModule(Annotator):
    name='stanfordnlp'
    def __init__(self, state_manager: StateManager, timeout=1.5, url=None, input_annotations = []):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url, input_annotations=input_annotations)

    def get_default_response(self, input_data: dict = None):
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        return {
            'nouns': [],
            'nounphrases': [],
            'proper_nouns': [],
        }

    def execute(self, input_data: dict = None):
        """
        If input_data is not None, run StanfordNLP on input_data. Otherwise, run on user utterance.

        @return: a dict with the keys:
            'nouns' -> list of strings
            'nounphrases' -> list of strings
            'proper_nouns' -> list of strings
        """
        if input_data is None:
            user_utterance = self.state_manager.current_state.text
            input_data = {'text': user_utterance}
        if not input_data['text']:
            return self.get_default_response()
        stanfordnlp_output = self.remote_call(input_data)
        if stanfordnlp_output is None:
            default_response = self.get_default_response()
            logger.info(f'{type(self).__name__} using default response: {default_response}')
            return default_response
        stanfordnlp_output = json.loads(stanfordnlp_output['response'])
        return {
            'nouns': get_nouns(stanfordnlp_output),
            'nounphrases': get_nps(stanfordnlp_output),
            'proper_nouns': get_proper_nouns(stanfordnlp_output),
        }
