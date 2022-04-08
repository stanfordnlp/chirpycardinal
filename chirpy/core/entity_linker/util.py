"""This file contains some functions and constants used in the entity linker"""

import logging
from typing import Set, Dict, List
from text2digits import text2digits
from typing import Optional
from chirpy.core.util import remove_punc, replace_phrase
from chirpy.core.latency import measure

t2d = text2digits.Text2Digits()

logger = logging.getLogger('chirpylogger')


NUMBER_ALTERNATIVES = [
    {'1', 'one', 'i'},
    {'2', 'two', 'ii'},
    {'3', 'three', 'iii'},
    {'4', 'four', 'iv'},
    {'5', 'five', 'v'},
    {'6', 'six', 'vi'},
    {'7', 'seven', 'vii'},
    {'8', 'eight', 'viii'},
    {'9', 'nine', 'ix'},
    {'10', 'ten', 'x'},

    {'first', '1st'},
    {'second', '2nd'},
    {'third', '3rd'},
    {'fourth', '4th'},
    {'fifth', '5th'},
    {'sixth', '6th'},
    {'seventh', '7th'},
    {'eighth', '8th'},
    {'ninth', '9th'},
    {'tenth', '10th'},

    {'the first', 'the 1st', 'i'},
    {'the second', 'the 2nd', 'ii'},
    {'the third', 'the 3rd', 'iii'},
    {'the fourth', 'the 4th', 'iv'},
    {'the fifth', 'the 5th', 'v'},
    {'the sixth', 'the 6th', 'vi'},
    {'the seventh', 'the 7th', 'vii'},
    {'the eighth', 'the 8th', 'viii'},
    {'the ninth', 'the 9th', 'ix'},
    {'the tenth', 'the 10th', 'x'},
]


SPAN_ALTERNATIVES = [
    {'spider man', 'spider-man', 'spiderman'},
    {'brothers', 'bros'},
    {'versus', 'vs', 'v'},
    {'doctor', 'dr'},
    {'mister', 'mr'},
    {'junior', 'jnr', 'jr'},
] + NUMBER_ALTERNATIVES


def singularize_pluralnoun(token: dict) -> Optional[str]:
    """
    Input:
        token: A dict representing the token (with keys 'originalText', 'lemma', 'pos'), as given by corenlp.
            If we didn't run corenlp, just has key 'originalText'.
    Return:
         If token is a plural noun (NNS), and we can obtain a singular version that's different to the originalText
         (either by using the lemma, or by removing 's'), return the singular version. Otherwise, return None.
    """
    pos_tag = token.get('pos', None)
    lemma = token.get('lemma', None)

    # If we have the pos tag and it's not plural noun, return None
    if pos_tag is not None and pos_tag != 'NNS':
        return None

    # If we have the lemma and it's different to the original text, return the lemma
    if lemma is not None and lemma != token['originalText']:
        return token['lemma']

    # If the originalText ends with s, return the version without the s
    if token['originalText'].endswith('s'):
        singular = token['originalText'][:-1]
        if singular:
            return singular

    return None


def get_singular_versions(span: str, corenlp_tokens: List[dict]) -> Set[str]:
    """
    If span contains any plural nouns (and is length 3 or less), return a list of alternative versions, that
    singularize the plural nouns.

    e.g. 'golden retrievers' -> {'golden retriever'}

    @param span: a span in the user's utterance
    @param corenlp_tokens: List of dicts, each representing a token, from the corenlp annotator.
    @return: set of alternative forms of span
    """
    corenlp_origtoken2tokeninfo = {token['originalText']: token for token in corenlp_tokens}  # str -> dict
    span_tokens = span.split()  # list of strings

    # To avoid generating too many candidate spans (which makes the ES query slower), only singularize spans of 3 or
    # fewer words. Most entities of length 4 or more are titles of e.g. movies/books which users don't tend to pluralize
    if len(span_tokens) > 3:
        return set()

    # For span tokens that are plural nouns, singularize them
    singularized_spantokens = [singularize_pluralnoun(corenlp_origtoken2tokeninfo.get(t, {'originalText': t})) for t in span_tokens]  # list of str/None

    # Get a list of versions of span_tokens, with all possible combinations of the original/singularized plural nouns
    versions = [span_tokens]  # list of list of strings
    for (orig_token, singularized_token) in zip(span_tokens, singularized_spantokens):

        # If orig_token has no singularized version, continue
        if singularized_token is None:
            continue

        # For each version in versions, make a version that has singularized_token instead of orig_token
        new_versions = []
        for version in versions:
            new_version = [t if t != orig_token else singularized_token for t in version]
            new_versions.append(new_version)
        versions += new_versions

    versions = {' '.join(version) for version in versions}  # set of str
    return versions


def get_manual_span_alternative_versions(span: str) -> Set[str]:
    """
    If span contains any phrases in SPAN_ALTERNATIVES, return a list of additional alternative versions, that have all
    possible alternative versions of the phrases.

    e.g. 'i love spider man' -> {'i love spider man', 'i love spider-man', 'i love spiderman'}

    @param span: a span in the user's utterance
    @return: set of alternative forms of span
    """

    # To avoid generating too many candidate spans (which makes the ES query slower), only make alternative versions of
    # spans of 5 or fewer words.
    if len(span.split()) > 5:
        return set()

    # Get a list of versions of span, with all possible combinations of the different versions of the manually specified phrases
    versions = {span}  # set of strings

    for phrase_set in SPAN_ALTERNATIVES:
        for orig_phrase in phrase_set:

            # Do a fast string.contains check to see if orig_phrase is in span. If not, continue
            if orig_phrase not in span:
                continue

            # For each version in versions, and each alt_phrase in phrase_set, make a version that has alt_phrase instead of orig_phrase
            for alt_phrase in phrase_set:

                new_versions = set()
                for version in versions:

                    if orig_phrase not in version:
                        continue

                    # Don't replace 'i' with 'first', '1st, 'the first', 'the 1st' etc if it's the first word in the span
                    if orig_phrase == 'i' and version.split()[0] == 'i':
                        continue

                    new_version = replace_phrase(version, orig_phrase, alt_phrase)
                    new_versions.add(new_version)
                versions.update(new_versions)

    return versions


def add_alt_span_mapping(alt_span: str, orig_span: str, altspan2origspan: Dict[str, str], ngrams: Set[str]):
    """
    Add a mapping from alt_span to orig_span in altspan2origspan. Handles the case where orig_span is itself
    an alternative span. Makes sure that alt_span maps to something that is in ngrams.
    """
    if orig_span in ngrams:
        altspan2origspan[alt_span] = orig_span
    elif orig_span in altspan2origspan:
        altspan2origspan[alt_span] = altspan2origspan[orig_span]
    else:
        raise Exception(f'We transformed orig_span="{orig_span}" to alt_span="{alt_span}", '
                        f'but orig_span is neither in ngrams nor in altspan2origspan={altspan2origspan}')
    return altspan2origspan


def add_alternative_spans(spans_to_lookup: Set[str], altspan2origspan: Dict[str, str], alternative_generator, ngrams: Set[str]):
    """
    Applies the alternative_generator to the spans in spans_to_lookup to get alternative spans. The alternative spans
    are added to spans_to_lookup, and to the altspan2origspan mapping.

    @param spans_to_lookup: set of strings. The spans we will attempt to link to entities.
    @param altspan2origspan: dict mapping alt_span -> orig_span, where orig_span is a span in the user utterance, and
        alt_span is an alternative form.
    @param alternative_generator: function which takes a span (string) as input, and outputs a set of alternative spans
        (strings) to be added to the spans_to_lookup
    @param ngrams: set of strings; this defines what is an "original" span
    """
    new_spans_to_lookup = {span for span in spans_to_lookup}
    for span in spans_to_lookup:
        alt_spans = alternative_generator(span)  # set of strings
        for alt_span in alt_spans:
            if alt_span not in new_spans_to_lookup:
                new_spans_to_lookup.add(alt_span)
                altspan2origspan = add_alt_span_mapping(alt_span, span, altspan2origspan, ngrams)
    return new_spans_to_lookup, altspan2origspan


@measure
def add_all_alternative_spans(spans_to_lookup: Set[str], ngrams: Set[str], corenlp_tokens: List[dict] = []):
    """
    Add alternative versions of spans (e.g. vary number format, punctuation, plural/singular) to spans_to_lookup.

    @param spans_to_lookup: The spans we want to link
    @param ngrams: The ngrams as they appear in the original text
    @param corenlp_tokens: List of dicts, each representing a token, from the corenlp annotator.
    @return: spans_to_lookup: Same as before, but we have added alternative versions of some of the spans.
    @return: altspan2origspan: Dict mapping any new alternative span (str) to its original form (str), which is in ngrams
    """
    altspan2origspan = {}

    # Make alternative number format versions of any number-containing spans
    # e.g. the span "frozen two" is transformed to the alternative "frozen 2"
    @measure
    def add_number_alts():
         return add_alternative_spans(spans_to_lookup, altspan2origspan, lambda span: {t2d.convert(span)}, ngrams)
    spans_to_lookup, altspan2origspan = add_number_alts()

    # Make alternative versions from our list of manual alternative phrases
    @measure
    def add_manual_alts():
        return add_alternative_spans(spans_to_lookup, altspan2origspan, lambda span: get_manual_span_alternative_versions(span), ngrams)
    spans_to_lookup, altspan2origspan = add_manual_alts()

    # Make alternative punctuation-less versions of any punctuation-containing spans
    # e.g. the span "a dog's purpose" is transformed to the alternative "a dogs purpose"
    # User utterances typically only contain apostrophes
    @measure
    def add_punc_alts():
        return add_alternative_spans(spans_to_lookup, altspan2origspan, lambda span: {remove_punc(span)}, ngrams)
    spans_to_lookup, altspan2origspan = add_punc_alts()

    # For spans that contain a plural noun, make a version with the singular form
    # e.g. the span "golden retrievers" is transformed to the alternative "golden retriever"
    @measure
    def add_singular_alts():
        return add_alternative_spans(spans_to_lookup, altspan2origspan, lambda span: get_singular_versions(span, corenlp_tokens), ngrams)
    spans_to_lookup, altspan2origspan = add_singular_alts()

    return spans_to_lookup, altspan2origspan


def wiki_name_to_url(ent_name: str):
    """Given the official wikipedia article title (entity name), return the url"""
    return f"https://en.wikipedia.org/wiki/{ent_name.replace(' ', '_')}"


def wiki_url_to_name(url: str):
    """Given the wikipedia url, gives the official wikipedia article title (entity name)"""
    return url.replace('https://en.wikipedia.org/wiki/', '').replace('_', ' ')


def main():
    # Demo here
    import time

    text = 'king philip the 3rd'

    print('new:')
    t0 = time.time()
    print(sorted(get_manual_span_alternative_versions(text)))
    print(f'took {time.time() - t0} seconds')


if __name__ == '__main__':
    main()
