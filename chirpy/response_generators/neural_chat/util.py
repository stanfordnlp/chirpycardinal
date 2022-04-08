from typing import Optional

MAX_NUM_NEURAL_TURNS = 5
NUM_CONVO_OPENING_TURNS = 2
NEURAL_DECODE_CONFIG = { # todo: once all modules are updated to BLenderbot -- no need for janky name converstion code
    'temperature': 0.7,
    'top_k': 5,
    'top_p': 0.9,
}

BLACKLIST = ['my child', 'my parent', 'my father', 'my mother', 'my wife', 'my husband', 'my daughter', 'my son',
             'my family', 'my cat', 'my dog', 'my car', 'my job', 'i\'ve been studying', 'i\'m a', 'i work', 'i study',
             'i am', 'i live', 'i drive',  'i\'m going to go', 'i\'m going to visit', 'mall', 'woman', 'women', 'man', 'did you know',

             'girl', 'boy', 'african', 'european', 'asian', 'american', 'hookie', 'chevy', 'ford', 'toyota', 'honda', 'overrated',
             'co-worker', 'i live',
             'do for you', 'do your family', 'talk to your family', 'good friends', 'any friends', 'friend of mine',
             'you\'re not a' # 'you're not a friend of mine'
             ]

def is_two_part(response) -> bool:
    """Returns True iff response has at least two parts as indicated by punctuation marks."""
    num_puncs = len([char for char in response if char in ['.', ',', '!', '?']])
    return num_puncs >= 2

def is_short(response):
    return len(response.split()) < 7

def is_short_set(sentences):
    return is_short(" ".join(sentences))

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
