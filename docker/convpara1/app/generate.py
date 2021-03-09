import logging
import random

import torch
import torch.nn.functional as F
import os

from data_utils import SPECIAL_TOKENS, build_input_from_segments_tc
from transformers.modeling_outputs import CausalLMOutputWithCrossAttentions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)
print(os.getcwd())

def top_filtering(logits, top_k=0, top_p=0.0, threshold=-float('Inf'), filter_value=-float('Inf')):
    """ Filter a distribution of logits using top-k, top-p (nucleus) and/or threshold filtering
        Args:
            logits: logits distribution shape (batch_size, vocabulary size)
            top_k: <=0: no filtering, >0: keep only top k tokens with highest probability.
            top_p: <=0.0: no filtering, >0.0: keep only a subset S of candidates, where S is the smallest subset
                whose total probability mass is greater than or equal to the threshold top_p.
                In practice, we select the highest probability tokens whose cumulative probability mass exceeds
                the threshold top_p.
            threshold: a minimal threshold to keep logits
    """
    assert logits.dim() == 2
    top_k = min(top_k, logits.size(-1))
    if top_k > 0:
        # Remove all tokens with a probability less than the last token in the top-k tokens
        indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
        logits[indices_to_remove] = filter_value

    if top_p > 0.0:
        # Compute cumulative probabilities of sorted tokens
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumulative_probabilities = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

        # Remove tokens with cumulative probability above the threshold
        sorted_indices_to_remove = cumulative_probabilities > top_p
        # Shift the indices to the right to keep also the first token above the threshold
        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
        sorted_indices_to_remove[..., 0] = 0

        # sorted_indices_to_remove is shape (batch_size, vocab_size) containing bools corresponding to sorted_indices.
        # Each row has Falses, then Trues.
        # For each row, get the index (in sorted_indices_to_remove) of the last False
        num_falses = sorted_indices_to_remove.size(1) - sorted_indices_to_remove.sum(dim=1)  # num false per row
        last_false = num_falses - 1  # idx of last false per row. shape (batch_size)

        # For each row, get the vocab-index of the last "False" token (i.e. least prob token that won't be masked)
        least_prob_index = sorted_indices[range(sorted_indices.size(0)), last_false]  # shape (batch_size)

        # For each row, get the logit for the least probable unmasked token
        cutoff_logits = logits[range(sorted_indices.size(0)), least_prob_index]  # shape (batch_size)

        # For each row, set everything lower than cutoff_logits to filter_value
        indices_to_remove = logits < cutoff_logits.unsqueeze(1)
        logits[indices_to_remove] = filter_value

    indices_to_remove = logits < threshold
    logits[indices_to_remove] = filter_value

    return logits



def sample_paraphrase(entity, context, history, tokenizer, model, current_output=None,
                      device="cuda" if torch.cuda.is_available() else "cpu",
                    no_sample=False, max_length=50, min_length=1, temperature=0.7, top_k=0, top_p=0,
                    num_samples=1, seed=None):
    # Note: output tokens don't include EOS but the list of probabilities and the overall probability does include it
    if seed is not None:
        random.seed(seed)
        torch.random.manual_seed(seed)
        torch.cuda.manual_seed(seed)
    special_tokens_ids = tokenizer.convert_tokens_to_ids(SPECIAL_TOKENS)
    past = None

    if current_output is None:
        current_output = []
        current_output_string = ''
        final_prob = [1 for _ in range(num_samples)]
        seq_probs = [[] for _ in range(num_samples)]

    current_outputs = [[i for i in current_output] for _ in range(num_samples)]
    current_output_strings = ['' for _ in range(num_samples)]
    finished = [False for _ in range(num_samples)]

    instances = [build_input_from_segments_tc(matched_entity=entity, matched_context=context,
                                              history=history, reply=current_output,
                                              tokenizer=tokenizer, lm_labels=False, with_eos=finished[ino],
                                              pretokenized_reply=True)
                 for ino, current_output in enumerate(current_outputs)]

    #instance = build_input_from_segments_tc(personality, history, current_output, tokenizer, with_eos=False)
    maxlen = max([len(instance) if finished[ino] else len(instance) for ino, instance in enumerate(instances)])
    for instance in instances:
        instance.maxlen = maxlen
    input_ids = torch.tensor([instance.words  for instance in instances], device=device)
    token_type_ids = torch.tensor([instance.segment_tokens for instance in instances], device=device)

    for i in range(max_length):
        with torch.no_grad():
            output: CausalLMOutputWithCrossAttentions = model(input_ids, token_type_ids=token_type_ids, past_key_values=past)
            logits = output.logits
            past = output.past_key_values


        # now logits is shape (num_samples, seqlen, vocab_size)
        logits = logits[:, -1, :].squeeze(1)
        skewed_logits =  logits / temperature
        skewed_logits = top_filtering(skewed_logits, top_k=top_k, top_p=top_p)
        #logits[:, 220] = -float('inf')
        skewed_probs = F.softmax(skewed_logits, dim=-1)
        probs = F.softmax(logits, dim=-1)

        prev = torch.topk(skewed_probs, 1)[1] if no_sample else torch.multinomial(skewed_probs, 1)
        for idx, p in enumerate(prev):
            if i < min_length and p.item() in special_tokens_ids:
                while p.item() in special_tokens_ids:
                    if skewed_probs[idx].max().item() == 1:
                        logger.warning("Warning: model generating special token with probability 1.")
                        break  # avoid infinitely looping over special token
                    prev[idx] = torch.multinomial(skewed_probs[idx], num_samples=1)

        # Update which samples have finished
        input_ids = torch.tensor([[tokenizer.convert_tokens_to_ids('<pad>')] if f else [p.item()] for f, p in zip(finished, prev)], device=device)

        token_type_ids = torch.tensor([[tokenizer.convert_tokens_to_ids('<pad>')] if f else [tokenizer.convert_tokens_to_ids('<self>')] for f, p in zip(finished, prev)], device=device)

        last_token_probs = torch.tensor([probs[i, p.item()] for i, p in zip(range(num_samples), prev)])

        # Last generated token can be an EOS, but we want to include its probability
        for i in range(num_samples):
            if not finished[i]:
                seq_probs[i].append(last_token_probs[i].item())
                final_prob[i]*=last_token_probs[i].item()
        # If they've all finished, quit
        # Otherwise append the latest tokens and continue
        for ino, (current_output, p) in enumerate(zip(current_outputs, prev)):
            if not finished[ino]:
                current_output.append(p.item())
        current_output_strings = [tokenizer.decode(current_output, skip_special_tokens=True) for current_output in current_outputs]
        current_output_tokens = [tokenizer.convert_ids_to_tokens(current_output) for current_output in current_outputs]
        finished = [f or p.item() in special_tokens_ids for (f,p) in zip(finished, prev)]
        if all(finished):
            break


    return current_output_strings, final_prob, finished, current_output_tokens, seq_probs
