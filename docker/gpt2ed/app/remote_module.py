import os
import sys

# Add the transfer-learning-conv-ai dir to sys.path so we can import the modules inside
transfer_learning_conv_ai_path = os.path.abspath('transfer-learning-conv-ai')
sys.path = [transfer_learning_conv_ai_path]+sys.path

# Import the interact module inside
import interact

# Load model
MODEL = 'gpt2-medium'
MODEL_CHECKPOINT = 'models/Jan04_22-40-10_ip-172-31-71-210_gpt2-medium'
model, tokenizer = interact.load_model(MODEL, MODEL_CHECKPOINT)

required_context = ['history']

def get_required_context():
    return required_context

def handle_message(msg):
    try:
        history = msg['history']
        config = msg['config'] if 'config' in msg else {}  # dict
        config = interact.complete_config(config)
        responses, unfinished_responses, history_used = interact.batch_decode(model, tokenizer, history, config)
        output = {
            'responses': responses,  # list of strings
            'unfinished_responses': unfinished_responses,  # list of strings
            'history_used': history_used,  # list of strings
        }
    except Exception as e:
        print('Encountered error, which we will send back in output: ', str(e))
        output = {
            'error': True,
            'message': str(e),
        }
    return output



if __name__ == "__main__":
    msg = {
        'history': ['i am having such a bad day today!']
    }
    result = handle_message(msg)
    print(result)