from simpletransformers.classification import ClassificationModel
from scipy.special import softmax
import torch

model = ClassificationModel('roberta', 'models/baseline/', use_cuda=False,
    args={'sliding_window': True,
        'fp16': False,
        'reprocess_input_data': True,
        'use_multiprocessing': False,
        'device': torch.device("cuda")})
required_context = ['utterance']
device = torch.device('cuda')
model.model.to(device)

def get_required_context():
    return required_context

def handle_message(msg):
    print(">>>>>>>>>>>>>>>>>>>>DEVICE>>>>>>>>>>>>>>>>")
    print(model.device)
    utterance = msg['utterance']
    print(f'starting prediction for utterance {utterance}')

    # The model takes in a batch and returns predictions for the entire batch
    predictions, raw_outputs = model.predict([utterance])
    print(f'predicted raw label is {predictions}')
    label_dict = {0:"not_question", 1: "question"}

    '''
    look @ binary decision
    '''
    labels = [label_dict[pred] for pred in predictions]

    label = labels[0]
    print(f'predicted label for utterance {utterance} is {label}')
    return [softmax(output).tolist()[0][1] for output in raw_outputs]

if __name__ == "__main__":
    msg = {
        'utterance': "my day was good how was yours"
    }
    result = handle_message(msg)
    print(result)