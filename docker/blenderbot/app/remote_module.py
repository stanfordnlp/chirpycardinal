from parlai.core.agents import create_agent_from_model_file
from itertools import zip_longest
# Load model
MODEL = 'blender_distilled/blender_distilled.pth.checkpoint'
blender_agent = create_agent_from_model_file(MODEL, opt_overrides={
    "model": "internal:cgen",                                                             
    "skip_generation": False,
    "inference": "delayedbeam",
    "beam_delay": 25,
    "beam_block_list_filename": "/deploy/app/parlai/resources/banned_words.txt"
    })

HF_TO_PARLAI_MAP = {
        "num_return_sequences": "beam_size",
        "temperature": "temperature",
        "top_k": "topk",
        "top_p": "topp",
        "min_length": "beam_min_length"
        }

import logging
logger = logging.getLogger(__file__)

required_context = ['history']

DEFAULT_CONFIG = {
    "topk": 5,
    "temperature": 0.7,
    "topp": 0.9,
    "beam_min_length": 20,
    "beam_size": 10
} # TODO

def update_config(config):
    logger.warn("Using map from GPT2ED config keys to BlenderBot config keys. This is deprecated and should be simplified to the original implementation in the GPT2ED remote module  once all modules switch to using BlenderBot.")
    """
        Keys to update:
            num_return_sequences -> beam_size
            temperature -> temperature
            top_k -> topk
            top_p -> topp
            min_length = beam_min_length

    """
    final_config = DEFAULT_CONFIG
    for key in config:
        if key in HF_TO_PARLAI_MAP:
            final_config[HF_TO_PARLAI_MAP[key]] = config[key]
        else:
            logger.warn(f"Key {key} not supported; omitting from configuration.")
    return final_config

def get_required_context():
    return required_context

def handle_message(msg):
    try:
        history = msg['history']
        config = update_config(msg['config'] if 'config' in msg else {})  # dict
        prefix = msg.get('prefix', None)

        blender_agent.opt.update(config) 
        print("Using history", history)
        print("Using config", config) 
        print(f"Using prefix '{prefix}'")
        blender_agent.reset()
        pairs = zip_longest(*[iter(history)]*2)

        for user, bot in pairs:
            blender_agent.observe({'text': user, 'episode_done': False})
            if bot:
                blender_agent.history.add_reply(bot)

        response_info = blender_agent.act(prefix_text=prefix)
        responses, response_probabilities = list(zip(*response_info['beam_texts']))
        output = {
            'responses': responses,  # list of str
            'response_probabilities': response_probabilities,
        }
    except Exception as e:
        import traceback
        print('>>>!! Encountered error, which we will send back in output: ', str(e))
        output = {
            'error': True,
            'message': str(e),
        }
        traceback.print_exc()
    return output



if __name__ == "__main__":
    msg = {
        'history': ['i am having such a bad day today!']
    }
    result = handle_message(msg)
    print(result)
