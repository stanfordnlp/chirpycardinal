from simpletransformers.classification import ClassificationModel


model = ClassificationModel('roberta', 'models/roberta/', use_cuda=False,
    args={'sliding_window': True,
        'fp16': False,
        'reprocess_input_data': True,
        'use_multiprocessing': False})
required_context = ['utterance']

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
    label_to_emotion = {0: 'grateful', 1: 'ashamed', 2: 'nostalgic', 3: 'hopeful', 4: 'anticipating', 5: 'impressed',
                        6: 'furious', 7: 'sad', 8: 'jealous', 9: 'annoyed', 10: 'embarrassed', 11: 'excited',
                        12: 'content', 13: 'caring', 14: 'guilty', 15: 'faithful', 16: 'afraid', 17: 'proud',
                        18: 'prepared', 19: 'devastated', 20: 'disappointed', 21: 'lonely', 22: 'confident',
                        23: 'sentimental', 24: 'joyful', 25: 'anxious', 26: 'terrified', 27: 'trusting', 28: 'angry',
                        29: 'apprehensive', 30: 'disgusted', 31: 'surprised'}

    emotions = [label_to_emotion[pred] for pred in predictions]

    emotion = emotions[0]
    print(f'predicted emotion for utterance {utterance} is {emotion}')
    return emotion

if __name__ == "__main__":
    msg = {
        'utterance': "I felt guilty when I was driving home one night and a person tried to fly into my lane_comma_ and didn't see me. I honked and they swerved back into their lane_comma_ slammed on their brakes_comma_ and hit the water cones."
    }
    result = handle_message(msg)
    print(result)