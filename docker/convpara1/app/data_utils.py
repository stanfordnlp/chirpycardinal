import re
from itertools import chain, repeat, islice
from typing import List, Optional, Union

from dataclasses import dataclass
import logging
from typing import List, Optional

logger = logging.getLogger(__file__)

SPECIAL_TOKENS = ["<bos>", "<eos>", "<self>", "<other>", "<context>", "<entity>", "<pad>"]
ATTR_TO_SPECIAL_TOKEN = {'bos_token': '<bos>', 'eos_token': '<eos>', 'pad_token': '<pad>',
                         'additional_special_tokens': ('<self>', '<other>', '<context>', '<entity>')}
MASKED_INDEX = -100


def add_special_tokens_(model, tokenizer):
    """ Add special tokens to the tokenizer and the model if they have not already been added. """
    orig_num_tokens = len(tokenizer.encoder)
    num_added_tokens = tokenizer.add_special_tokens(ATTR_TO_SPECIAL_TOKEN) # doesn't add if they are already there
    if num_added_tokens > 0:
        model.resize_token_embeddings(new_num_tokens=orig_num_tokens + num_added_tokens)
@dataclass
class Segment:
    segment_token: int
    data_tokens: List[int]
    set_lm_labels: bool = False

    @property
    def words(self):
        return [self.segment_token] + self.data_tokens

    @property
    def segment_tokens(self):
        return [self.segment_token] * len(self.words)

    @property
    def lm_labels(self):
        if self.set_lm_labels:
            return [MASKED_INDEX] + self.data_tokens
        else:
            return [MASKED_INDEX] * len(self.words)

    def info(self):
        print(self.segment_token, len(self.data_tokens), self.data_tokens)

@dataclass
class SegmentSequence:
    input_segments: List[Segment]
    eos_token: int
    pad_token: int
    with_eos: bool = True
    _maxlen: Optional[int] = None

    @property
    def words(self):
        #for s in self.input_segments:
        #    print(s.segment_token, len(s.data_tokens), s.data_tokens)
        #print()
        if self.with_eos:
            assert self.maxlen
            return list(islice(chain(
                *(segment.words for segment in self.input_segments),
                [self.eos_token],
                repeat(self.pad_token)),
                self.maxlen))
        else:
            return list(chain(*(segment.words for segment in self.input_segments)))


    @property
    def segment_tokens(self):
        if self.with_eos:
            assert self.maxlen
            return list(islice(
                chain(*(segment.segment_tokens for segment in self.input_segments),
                      [self.eos_token], repeat(self.pad_token)),
                self.maxlen))
        else:
            return list(chain(*(segment.segment_tokens for segment in self.input_segments)))


    @property
    def lm_labels(self):
        if self.with_eos:
            assert self.maxlen
            return list(islice(
                chain(*(segment.lm_labels for segment in self.input_segments),
                      [self.eos_token], repeat(MASKED_INDEX)),
                self.maxlen))
        else:
            return  list(chain(*(segment.lm_labels for segment in self.input_segments)))

    @property
    def mc_token_id(self):
        return len(self) - 1

    @property
    def maxlen(self):
        return self._maxlen

    @maxlen.setter
    def maxlen(self, val):
        assert val>=len(self)
        self._maxlen = val

    def __len__(self):
        if self.with_eos:
            return sum(len(segment.words) for segment in self.input_segments) + 1
        else:
            return sum(len(segment.words) for segment in self.input_segments)

@dataclass
class InputInstance:
    gold_sequence : SegmentSequence
    distractors: List[SegmentSequence]
    _maxlen: Optional[int] = None

    @property
    def words(self):
        return [self.gold_sequence.words] + [segment.words for segment in self.distractors]

    @property
    def segment_tokens(self):
        return [self.gold_sequence.segment_tokens] + [segment.segment_tokens for segment in self.distractors]

    @property
    def lm_labels(self):
        return [self.gold_sequence.lm_labels] + [segment.lm_labels for segment in self.distractors]

    @property
    def mc_token_ids(self):
        return [self.gold_sequence.mc_token_id] + [segment.mc_token_id for segment in self.distractors]

    @property
    def mc_label(self):
        return 0

    @property
    def maxlen(self):
        return self._maxlen

    @maxlen.setter
    def maxlen(self, val):
        self._maxlen = val
        self.gold_sequence.maxlen = val
        for d in self.distractors:
            d.maxlen = val

    def __len__(self):
        return max(len(self.gold_sequence), *(len(d) for d in self.distractors), 0)

def pad_instances(instances: List[Union[SegmentSequence, InputInstance]]):
    maxlen = max(len(i) for i in instances)
    for i in instances:
        i.maxlen = maxlen
    return instances

def convert_to_alexa_asr(sentence: str):
    alexa_asr_sentence = re.sub(r"[^\w\d'.\s]+", '', sentence) #remove punctuations except . and '
    alexa_asr_sentence = re.sub(r"(?P<pre>[\w\s\d]{2,})[.]+(?P<post>[\s]|$)", r'\g<pre> \g<post>', alexa_asr_sentence) #remove . except when they are used in an abbreviation (i.e. without space separation)
    alexa_asr_sentence = re.sub(r"(?P<pre>[\s])[.]+", r'\g<pre>', alexa_asr_sentence) #remove . except when they are used in an abbreviation (i.e. without space separation)
    alexa_asr_sentence = re.sub(r"[\s]+", " ", alexa_asr_sentence)
    alexa_asr_sentence = alexa_asr_sentence.lower().strip()
    return alexa_asr_sentence

def build_input_from_segments_tc(matched_entity: str, matched_context: str, history: List[str], reply: Union[str, List[int]], tokenizer, lm_labels=False, with_eos=True, pretokenized_reply=False, alexa_asr_input=False):
    bos_token, eos_token, self_token, other_token, context_token, entity_token = tokenizer.convert_tokens_to_ids(SPECIAL_TOKENS[:-1])
    pad_token = tokenizer.convert_tokens_to_ids('<pad>')

    #Each of the following return values is a list of 3-tuple (word_token, segment_token, lm_label)
    matched_entity_segment = Segment(entity_token, tokenizer.tokenize_to_ids(matched_entity))
    matched_context_segment = Segment(context_token , tokenizer.tokenize_to_ids(matched_context))
    history_segments = []
    for r_id, r_turn in enumerate(reversed(history)):
        other = r_id % 2 == 0
        segment_token = other_token if other else self_token
        text = convert_to_alexa_asr(r_turn) if (other and alexa_asr_input) else r_turn
        tokens = tokenizer.tokenize_to_ids(text)
        history_segments.append(Segment(segment_token, tokens))
    history_segments = list(reversed(history_segments))

    if pretokenized_reply:
        reply_segment = Segment(self_token, reply, set_lm_labels=lm_labels)
    else:
        reply_segment = Segment(self_token , tokenizer.tokenize_to_ids(reply), set_lm_labels=lm_labels)

    sequence = SegmentSequence([matched_entity_segment, matched_context_segment] + history_segments + [reply_segment],
                               eos_token, pad_token,with_eos)
    return sequence