import os
import sys

# Add the transfer-learning-conv-ai dir to sys.path so we can import the modules inside
transfer_learning_conv_ai_path = os.path.abspath('transfer-learning-conv-ai')
sys.path = [transfer_learning_conv_ai_path]+sys.path


import torch

import torch.nn.functional as F
import transformers
from transformers import AutoTokenizer, AutoModelForSequenceClassification, GPT2LMHeadModel, GPT2Tokenizer

import os
import multiprocessing as mp
mp.set_start_method('spawn')

from itertools import chain


MODEL_CHECKPOINT = 'models/gpt2ed'

gpt2ed_model = GPT2LMHeadModel.from_pretrained(MODEL_CHECKPOINT)
gpt2ed_tokenizer = GPT2Tokenizer.from_pretrained(MODEL_CHECKPOINT)
UPDOWN_TOKENIZER = AutoTokenizer.from_pretrained("microsoft/DialogRPT-updown")
UPDOWN_MODEL = AutoModelForSequenceClassification.from_pretrained("microsoft/DialogRPT-updown")

required_context = ['context', 'responses']

device = 'cpu'
gpt2ed_model.to(device)
UPDOWN_MODEL.to(device)

def build_input_from_segments(history, reply, tokenizer, lm_labels=False, with_eos=True):
    """ Build a sequence of input from 2 segments: history and last reply.
    history: list of list of int
    reply: list of int
    """
    bos, eos, speaker1, speaker2 = tokenizer.convert_tokens_to_ids(["<bos>", "<eos>", "<speaker1>", "<speaker2>"])

    instance = {}

    # here sequence is a list of lists of int
    # the first lists are the history utterances
    # the last list is the reply (maybe with eos at the end)
    sequence = history + [reply + ([eos] if with_eos else [])]

    # here sequence is a list of lists of int, as before
    # but now the history and reply lines start with alternating speaker1/speaker2 tokens
    # the reply is always speaker2
    # the first history line also starts with bos
    sequence = [
      ([bos] if i==0 else []) + [speaker2 if (len(sequence)-i) % 2 else speaker1] + s
      for i, s in enumerate(sequence)]

    instance["input_ids"] = list(chain(*sequence))  # list of ints
    instance["token_type_ids"] = [speaker2 if i % 2 else speaker1 for i, s in enumerate(sequence) for _ in s]  # list of ints (all speaker1 or speaker2, starting with speaker1), same length as input_ids
    instance["mc_token_ids"] = len(instance["input_ids"]) - 1  # int, the length of the whole input. it gives the location of the last hidden state, from which we compute the multiple choice loss

    instance["lm_labels"] = [-100] * len(instance["input_ids"])  # -1 for the whole sequence if lm_labels=False
    if lm_labels:
        instance["lm_labels"] = ([-100] * sum(len(s) for s in sequence[:-1])) + [-100] + sequence[-1][1:]  # -1 for the masked parts, then the actual targets for the reply

    return instance

def process_input_pair_for_gpt2ed(context, hypothesis):
    context_ids = [gpt2ed_tokenizer.encode(sent) for sent in context]
    hypothesis_ids = gpt2ed_tokenizer.encode(hypothesis)
    model_input = build_input_from_segments(context_ids, hypothesis_ids, gpt2ed_tokenizer, lm_labels=True)
    return model_input

# @ unused
def process_input_pair_for_ranker(tokenizer, context, hypothesis):
    model_input = tokenizer.encode(tokenizer.eos_token.join(context) + tokenizer.eos_token + hypothesis,
                                   return_tensors="pt")
    return model_input


def pad_sequence(seq, padding_value=0):
    lengths = [len(a) for a in seq]
    max_len = max(lengths)
    out = [torch.tensor(sent + [padding_value] * (max_len - len(sent))) for sent in seq]
    return torch.stack(out, dim=0)

def pad_tensor(seq, padding_value=0):
    lengths = [a.size(-1) for a in seq]
    max_len = max(lengths)
    out = [torch.cat([sent, padding_value * torch.ones(max_len - sent.size(-1), dtype=int).unsqueeze(0)], dim=-1) for sent in seq]
    return torch.LongTensor(torch.cat(out, dim=0))

def score_gpt2ed_batch(inputs, mask, labels):
    outputs = gpt2ed_model(inputs, attention_mask=mask, labels=labels)
    _, _logits = outputs[:2]
    _labels = torch.cat([inputs[:, 1:], inputs[:, :1] * 0], dim=1) # shift inputs one position to the left and flatten
    _labels[_labels == -1.] = 0
    raw_nll = F.cross_entropy(_logits.permute(0, 2, 1), _labels, ignore_index=0, reduction='none')
    loss_real_avg = raw_nll.sum(dim=-1) / mask.sum(dim=-1, keepdim=True).squeeze(-1) #
    return torch.exp(-loss_real_avg).tolist()

def score_ranker_batch(ranker, model_input):
    result = ranker(model_input, return_dict=True)
    return torch.sigmoid(result.logits).squeeze(1).tolist()

def get_required_context():
    return required_context


BATCH_SIZE = 8
def handle_message(msg):
    try:
        context = msg['context']
        responses = msg['responses']
        output = {
                "score": [],
                "updown": [],
                }

        jobs = [(process_input_pair_for_gpt2ed(context, hypothesis), process_input_pair_for_ranker(UPDOWN_TOKENIZER, context, hypothesis))for hypothesis in responses]
        with torch.no_grad():
            inputs = pad_sequence([elem["input_ids"] for elem, _, in jobs], padding_value=0).to(device)
            labels = pad_sequence([elem["lm_labels"] for elem, _, in jobs], padding_value=-100).to(device)
            mask = (inputs != 0).float().to(device)
            for inputs, mask, labels in zip(torch.split(inputs, BATCH_SIZE, dim=0), torch.split(mask, BATCH_SIZE, dim=0), torch.split(labels, BATCH_SIZE, dim=0)):
                output["score"] += score_gpt2ed_batch(inputs, mask, labels)
            inputs = pad_tensor([elem for _, elem in jobs], padding_value=0).to(device)
            # for ranker in [UPDOWN_MODEL, DEPTH_MODEL, WIDTH_MODEL]:
            for ranker in [UPDOWN_MODEL]:
                scores = []
                for model_input in torch.split(inputs, BATCH_SIZE, dim=0):
                    scores += score_ranker_batch(ranker, model_input)
                if ranker == UPDOWN_MODEL:
                    output["updown"] = scores
                elif ranker == DEPTH_MODEL:
                    output["depth"] = scores
                else:
                    output["width"] = scores

    except Exception as e:
        print('Encountered error, which we will send back in output: ', str(e))
        output = {
            'error': True,
            'message': str(e),
        }
        import traceback
        traceback.print_exc()

    return output

if __name__ == "__main__":
    msg = {
        'context': ['do you lile bots?','i love chirpy cardinal social bot!'],
        'responses': ['cool, me too! did you know that it was developed by some very cool people?',
                    'that sounds really interesting! i too would like to make a chatbot someday.',
                    'sounds boring.']
    }
    result = handle_message(msg)
    print(result)
