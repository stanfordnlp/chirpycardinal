from data_utils import add_special_tokens_
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from functools import lru_cache
import random, torch
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)
def set_random_seed(seed):
    if seed != 0:
        random.seed(seed)
        torch.random.manual_seed(seed)
        torch.cuda.manual_seed(seed)


def load_model(args):
    set_random_seed(args.seed)

    logger.info("Get pretrained model and tokenizer")
    #tokenizer_class, model_class = (GPT2Tokenizer, GPT2LMHeadModel) if args.model == 'gpt2' else (
    #    OpenAIGPTTokenizer, OpenAIGPTLMHeadModel)
    tokenizer_class, model_class = GPT2Tokenizer, GPT2LMHeadModel
    tokenizer = tokenizer_class.from_pretrained(args.model_checkpoint)
    tokenizer.tokenize_to_ids = lru_cache(maxsize=None, typed=False)(
        lambda seq: tokenizer.convert_tokens_to_ids(tokenizer.tokenize(seq)))
    try:
        model = model_class.from_pretrained(os.path.join(args.model_checkpoint, args.checkpoint_filename), config=args.model_checkpoint)
    except AttributeError:
        model = model_class.from_pretrained(args.model_checkpoint)
    model.to(args.device)
    add_special_tokens_(model, tokenizer)
    return tokenizer, model