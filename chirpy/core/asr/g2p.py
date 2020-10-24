# This file contains the g2p function that converts a span to one phonetic representation (grapheme to phoneme).
# This function is used for indexing anchortexts and when input spans are looked up in the index.

from functools import lru_cache
import os
import pickle
from typing import List

# Load the pickled cmudict
# This is derived from the CMUDict pronunciation dictionary, which maps spelling of a word to potential phoneme pronuncations
with open(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cmudict.pkl'), 'rb') as f:
    CMUDICT = pickle.load(f)

def simple_g2p(span: str) -> List[str]:
    """ A simple dictionary-based grapheme to phoneme algorithm """
    lattice = [CMUDICT.get(x, ['?']) for x in span.lower().split()]
    if len(lattice) == 0:
        return []

    res = lattice[0][0].split()
    for x in lattice[1:]:
        res.append(' ')
        res.extend(x[0].split())
    return res


@lru_cache(maxsize=32768)
def g2p(span: str, g2p_module = None) -> List[str]:
    """ Use the remote g2p module for grapheme to phoneme conversion when simple dict-based method fails """
    simple_phonemes = simple_g2p(span)
    if '?' not in simple_phonemes:
        return simple_phonemes

    try:
        phonemes = g2p_module.execute(span)
        if phonemes is None:
            return simple_phonemes
        return phonemes
    except Exception as ex:
        return simple_phonemes

if __name__ == "__main__":
    from chirpy.core.asr.index_phone_to_ent import MockG2p
    mock_g2p_module = MockG2p()
    print(g2p('there eyes of skywalker', mock_g2p_module))
    print(g2p('the rise of skywalker', mock_g2p_module))
    print(g2p('love you 3000', mock_g2p_module))

