import collections
import re
import torch

from itertools import tee
from nltk.tokenize import sent_tokenize

_Prediction = collections.namedtuple("Prediction", ["start_index", "end_index", "score"])


def split_context(body, token_limit, tokenizer):
    """Splits the big context into smaller contexts with each context having no more than token_limit tokens."""
    # There is no overlap between body splits. We assume that the answer we are looking
    # for does not span more than one sentence. In the future, we might need to add doc_stride to have an overlap
    # between contexts.
    sentence_tokens = sent_tokenize(body)   # Gives us a list of sentences.
    sentence_iter = iter(sentence_tokens)   # Gives us an iterator of sentences.
    contexts = []
    while True:
        context, sentence_iter = get_context(sentence_iter, token_limit, tokenizer)
        contexts.append(context)
        if not sentence_iter:
            break
    # A sanity check for the total number of sentences in the original context is equal to the sum of the number of
    # sentences in the smaller contexts.
    assert sum([count_words(sentence) for sentence in contexts]) == sum([count_words(sentence) for sentence in sentence_tokens])
    return contexts


def get_context(sentence_iter, token_limit, tokenizer):
    context = ''
    while True:
        # Saving a copy of the iterator in case we made a mistake
        # by stepping to the next sentence.
        sentence_iter, sentence_iter_copy = tee(sentence_iter)
        next_sentence = next(sentence_iter, None)
        if next_sentence:
            new_context = context + ' ' + next_sentence
            if is_within_token_limit(new_context, token_limit, tokenizer):
                context = new_context
            else:
                return context, sentence_iter_copy
        else:
            return context, None


def count_words(string):
    """Counts the number of words in a string."""
    return len(string.split())


def is_within_token_limit(context, token_limit, tokenizer):
    """Counts the total number of tokens in the text snippet."""
    return len(tokenizer.convert_ids_to_tokens(tokenizer.encode(context))) < token_limit


def to_list(tensor):
    return tensor.detach().cpu().tolist()


def get_best_indices_score(logits, n_best_size, context_start, context_end):
    """Get the n-best logits from a list."""
    index_and_score = sorted(enumerate(logits), key=lambda x: x[1], reverse=True)
    best_indices_score = []
    for i in range(len(index_and_score)):
        if len(best_indices_score) == n_best_size:
            break
        index = index_and_score[i][0]
        # The start_index or the end_index cannot include the question which is redundant in the answer.
        if (index >= context_start) and (index <= context_end):
            best_indices_score.append(index_and_score[i])
    assert(len(best_indices_score) <= n_best_size)
    return best_indices_score


def BERT_span(question, context, tokenizer, model, n_best_size=10, max_answer_length=30):
    """Returns the answer which is a span in the context and its score."""
    input_text = question + " [SEP] " + context 
    input_ids = tokenizer.encode(input_text)
    all_tokens = tokenizer.convert_ids_to_tokens(input_ids)
    token_type_ids = [0 if i <= input_ids.index(102) else 1 for i in range(len(input_ids))]
    context_start = len(tokenizer.convert_ids_to_tokens(tokenizer.encode(question)))
    context_end = len(all_tokens) - 2
    outputs = model(torch.tensor([input_ids], device='cuda:0'), \
        token_type_ids=torch.tensor([token_type_ids], device='cuda:0'))
    output = [to_list(output) for output in outputs]
    start_logits, end_logits = output

    predictions = []
    predictions.append(_Prediction(
        start_index=0, 
        end_index=0,
        score = start_logits[0][0] + end_logits[0][0],
    ))   
    
    start_indices = get_best_indices_score(start_logits[0], n_best_size, context_start, context_end)
    end_indices = get_best_indices_score(end_logits[0], n_best_size, context_start, context_end)      
    for start_index in start_indices:
        for end_index in end_indices:
            if start_index[0] <= end_index[0]:
                length = end_index[0] - start_index[0] + 1
                if length <= max_answer_length:
                    predictions.append(_Prediction(
                        start_index=start_index[0], 
                        end_index=end_index[0], 
                        score = start_index[1] + end_index[1],
                    ))
    predictions = sorted(predictions, key=lambda x: x.score, reverse=True)
    answers = []
    for pred in predictions:
        if pred.start_index == 0 or len(answers) == n_best_size:
            break
        else:
            answer = ' '.join(all_tokens[pred.start_index: pred.end_index + 1])
            answers.append((post_process(answer), pred.score))
    assert(len(answers) <= n_best_size)
    return answers


def post_process(answer):
    """Cleans the answers by remove hashes, and adding spaces wherever necessary. Also
    removes non-ascii characters present in the answer.
    """
    answer = ''.join([i if ord(i) < 128 else '' for i in answer])
    answer = re.sub(r'\s+', ' ', answer)
    answer = re.sub(r'\s?##', '', answer)
    # Remove space after these characters.
    answer = re.sub(r'(\(|{|\[|<|\$|-|@|\')\s', r'\1', answer)
    # Remove space before these characters.
    answer = re.sub(r'\s(,|\.|:|"|\]|\)|}|>|;|-|@|\')', r'\1', answer)
    # Add a space after fullstop.
    answer = re.sub(r'\.', r'. ', answer)
    # Remove duplicate whitespaces.
    answer = re.sub(r'\s+', ' ', answer) 
    return answer


def predict(question, context, tokenizer, model, n_best_size=10, max_answer_length=30):
    """Return the answers from each context."""
    answers = []
    token_limit = 512 - (len(tokenizer.convert_ids_to_tokens(tokenizer.encode(question))) + 3)
    for context in split_context(context, token_limit, tokenizer):
        answer_context = BERT_span(question, context, tokenizer, model, n_best_size, max_answer_length)
        if answer_context:
            answers += answer_context
    # answers = [] if there is No-Answer is the best answer in all chunks.
    return answers
