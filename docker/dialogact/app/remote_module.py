import json
import numpy as np
from scipy.special import softmax
from simpletransformers.classification import ClassificationModel

model = ClassificationModel('bert', 'models/midas-2', use_cuda=False,
    num_labels=24, 

    args={'sliding_window': True,
        'fp16': False,
        'reprocess_input_data': True,
        'use_multiprocessing': False})
required_context = ['instances']

def get_required_context():
    return required_context

def format_message(msg):
    return (msg['context'].lower())+" : EMPTY > "+(msg['utterance'].lower())

def handle_message(msg):
    """

    Args:
        msg (dict): with key
            'instances': List of dicts, each with keys
                'context': Bot's utterance in previous turn
                'utterance': User's utterance in current turn

    Returns:
        prob_dicts: list of dicts, where keys are dialog acts
                    and values are the predicted probabilities
    """
    print(">>>>>>>>>>>>>>>>>>>>DEVICE>>>>>>>>>>>>>>>>")
    print(model.device)
    instances = msg['instances']
    message_strs = list(map(format_message, instances))
    print(f'starting prediction for messages {message_strs}')
    predictions, raw_outputs = model.predict(message_strs) # raw_outputs is logits?
    raw_outputs = [raw_output.astype(np.float64) for raw_output in raw_outputs] # convert to float64 because float32 is not json serializable

    print(f'predicted raw label is {predictions}')
    label_to_act = {0: "statement", 1: "back-channeling", 2: "opinion", 3: "pos_answer", 4: "abandon",
                    5: "appreciation", 6: "yes_no_question", 7: "closing", 8: "neg_answer",
                    9: "other_answers", 10: "command", 11: "hold", 12: "complaint",
                    13: "open_question_factual", 14: "open_question_opinion", 15: "comment",
                    16: "nonsense", 17: "dev_command", 18: "correction", 19: "opening", 20: "clarifying_question",
                    21: "uncertain", 22: "non_compliant", 23: "open_question_personal"}

    pred_probas = list(map(softmax, raw_outputs))
    prob_dicts = [dict(zip(label_to_act.values(), pred[0])) for pred in pred_probas]

    return prob_dicts

if __name__ == "__main__":
    msg = {
        'instances': [{'context': 'what is your favorite movie', 
                       'utterance': 'finding nemo'},
                       {'context': 'what is your favorite color',
                        'utterance': 'blue'}]
    }
    result = handle_message(msg)
    print(result)
