from typing import Optional

MAX_NUM_GPT2ED_TURNS = 5

GPT2ED_DECODE_CONFIG = {
    'no_sample': False,
    'min_length': 4,  # in GPT2 tokens
    'max_length': 20,  # in GPT2 tokens
    'temperature': 0.7,
    'top_k': 0,
    'top_p': 0.9,
    'max_history_tokens': 800,  # in GPT2 tokens
    'num_samples': 20,
}


def is_two_part(response) -> bool:
    """Returns True iff response has at least two parts as indicated by punctuation marks."""
    num_puncs = len([char for char in response if char in ['.', ',', '!', '?']])
    return num_puncs >= 2

def question_part(response) -> Optional[str]:
    """Returns the question part of the utterance, if there is one. Otherwise returns None"""
    if '?' not in response:
        return None
    question_idx = response.index('?')
    response = response[:question_idx].strip()
    other_punc_indices = [i for i in range(len(response)) if response[i] in ['.', ',', '!']]
    if not other_punc_indices:
        return response
    last_other_punc_index = max(other_punc_indices)
    response = response[last_other_punc_index+1:].strip()
    return response



# if __name__ == "__main__":
#     print(question_part("that's so cool! what did you do?"))