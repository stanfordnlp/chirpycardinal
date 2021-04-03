from generate import sample_paraphrase
from model_loading_utils import load_model
import argparse
import logging
import torch

import sys
print("Python version", sys.version)
print("Pytorch version", torch.__version__)
# Load model
args = argparse.Namespace()
args.seed = 3421
args.model = 'gpt2'
args.model_checkpoint = 'model/'
#args.checkpoint_filename =
args.device = "cuda" if torch.cuda.is_available() else "cpu"
#args.device = "cuda"
logging.info(f"Using device {args.device}")
tokenizer, model = load_model(args)
logging.info(f"Loaded tokenizer and model")
required_context = ['entity']

def get_required_context():
    return required_context


def handle_message(msg):
    entity = msg.get('entity')
    background = msg.get('background', '')
    history = msg.get('history', [])
    given_config = msg.get('config', {})
    default_config_vars = {'no_sample': False,
                           'max_length': 40,
                           'min_length': 5,
                           'temperature': 0.95,
                           'top_k': 0,
                           'top_p': 0.8,
                           'num_samples': 4,
                           'seed': 4230}
    config = {}
    #utterances = zip(history[::2], history[1::2])
    #lengths = [len(u[0].split(' '))+len(u[1].split(' ')) for u in utterances]

    #for reversed(zip(utterances, lengths))
    for k, v in default_config_vars.items():
        config[k] = given_config.get(k, v)
    if config['temperature'] == 0:
        config['temperature'] = 1
    logging.info(f"Querying with \n entity = {entity} \n background = {background} \n history = {history} \n config = {config} ")
    generated_strings, prob, sample_finished, generated_tokens, seq_probs = sample_paraphrase(
        entity=entity,
        context=background,
        history=history,
        tokenizer=tokenizer,
        model=model,
        **config)
    logging.info(f"Got generations = {generated_strings}")

    # Fill in missing keys in config using defaults

    return {
        'paraphrases': generated_strings,
        'probabilities': prob,
        'paraphrase_ended': sample_finished,
        'paraphrase_tokens': generated_tokens,
        'paraphrase_token_probabilities': seq_probs,
    }


if __name__ == "__main__":
    msg = {'entity': 'Jesus',
 'background': '"That We call Jesus by that name because of multiple transliterations--a direct translation from the original "Yehoshua" would be "Joshua"',
 'history': ['Jesus (), also referred to as Jesus of Nazareth and Jesus Christ, was a first-century Jewish preacher and religious leader.. He is the central figure of Christianity.. Would you like to learn more about Jesus?',
  'i know that jesus i thought we were going to talk about jesus'],
 'config': {'device': 'cuda', 'num_samples': 4, 'max_length': 40, 'top_p':0.9, 'temperature':0.9}}
    result = handle_message(msg)
    print(result)
