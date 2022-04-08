from collections import Counter
from editdistance import eval as editdist
import re
from typing import List, Iterable
from chirpy.core.asr.g2p import g2p, CMUDICT

def remove_stress(phoneme_str: str) -> str:
    return re.sub(r'[0-9]', '', phoneme_str)


def span_to_lattice(span: str, g2p_module = None) -> List[List[str]]:
    """
    Convert a span to its lattice representation that captures multiple potential pronunciations.
    For each (space-separated) word in the span, there is a list in the output containing space-separated phonemes that
    correspond to potentially different pronunciations of that word.
    Optionally uses a neural remote module to catch words that aren't in the phonetic dictionary.
    For instance, "rotten tomato" -> [['R AA1 T AH0 N'], ['T AH0 M EY1 T OW2', 'T AH0 M AA1 T OW2']]
    """
    return [CMUDICT.get(x, [' '.join(g2p(x, g2p_module))]) for x in span.split()]

def lattice_to_phonemes(lattice: List[List[str]]) -> Iterable[str]:
    """
    Convert a lattice (list of possible pronunciations of each word) to all possible phonetic renderings of the entire span
    e.g., "rotten tomato" -> ['R AA1 T AH0 N T AH0 M EY1 T OW2', 'R AA1 T AH0 N T AH0 M AA1 T OW2']
    """
    if len(lattice) == 1:
        yield from lattice[0]
    else:
        for x in lattice[0]:
            for y in lattice_to_phonemes(lattice[1:]):
                yield ' '.join([x, y])


def get_lattice_similarity(lattice1: List[List[str]], lattice2: List[List[str]], threshold: float = 0.8,
                           ignore_stress: bool = False) -> float:
    """
    Compare two lattices to find the similarity ratio of the closest phonetic renderings of them
    "threshold" is the similarity we're trying to match to return a potential link, higher values help us avoid
    expensive computation for the actual similarity score.
    The range of the output is [0, 1], 0 being the least similar, and 1 indicating an identical phonetic rendering in
    the two lattices. This is from Python's difflib.SequenceMatcher, calculated as follows: Where T is the total number
    of elements in both sequences, and M is the number of matches, this is 2.0*M / T.
    See also: https://docs.python.org/3.7/library/difflib.html#difflib.SequenceMatcher.ratio
    """
    max_ratio = 0
    for p1 in lattice_to_phonemes(lattice1): # for each rendering from lattice1
        if ignore_stress:
            p1 = remove_stress(p1)
        c1 = Counter(p1.split())
        l1 = len(p1.split())
        p1 = p1.split()
        for p2 in lattice_to_phonemes(lattice2): # for each rendering from lattice 2
            # Jaccard similarity
            if ignore_stress:
                p2 = remove_stress(p2)
            c2 = Counter(p2.split())
            l2 = len(p2.split())
            if sum((c1 & c2).values()) * 2 / (l1 + l2) < threshold:
                # If the candidates can't pass an orderless filter, there's no use in getting an exact ratio from the
                # (more expensive) SequenceMatcher
                continue

            # m = SequenceMatcher(a=p1.split(), b=p2.split(), autojunk=False)
            # ratio = m.ratio()
            p2 = p2.split()
            ratio = 1 - editdist(p1, p2) / max(len(p1), len(p2))
            # ratio = (len(p1) + len(p2) - 2 * dist) / (len(p1) + len(p2))
            if ratio == 1:
                return 1

            if ratio > max_ratio:
                max_ratio = ratio
    return max_ratio

if __name__ == "__main__":
    from chirpy.core.asr.index_phone_to_ent import MockG2p

    mock_g2p_module = MockG2p()

    span1 = "Lamborghini"
    span2 = "laborgini"

    print('span1: ', span1)
    print('span2: ', span2)

    lattice1 = span_to_lattice(span1, mock_g2p_module)
    lattice2 = span_to_lattice(span2, mock_g2p_module)

    print('lattice1: ', lattice1)
    print('lattice2: ', lattice2)

    phonemes1 = lattice_to_phonemes(lattice1)
    phonemes2 = lattice_to_phonemes(lattice2)

    print('phonemes1: ', list(phonemes1))
    print('phonemes2: ', list(phonemes2))

    print("similarity: ", get_lattice_similarity(lattice1, lattice2, threshold=.8))
    print("similarity (stress-less): ", get_lattice_similarity(lattice1, lattice2, threshold=.8, ignore_stress=True))
