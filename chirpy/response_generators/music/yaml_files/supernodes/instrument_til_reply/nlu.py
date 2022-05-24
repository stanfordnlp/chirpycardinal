import logging
import random
import re

from chirpy.core.response_generator import Treelet
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType, AnswerType
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
from chirpy.response_generators.music.utils import WikiEntityInterface
from chirpy.response_generators.wiki2.wiki_utils import get_til_title
from chirpy.response_generators.music.state import ConditionalState
from chirpy.response_generators.music.music_helpers import ResponseType

def nlu_processing(rg, state, utterance, response_types):
	flags = {
		'thats': False,
		'did_not_know': False,
		'catch_all': False,
		'entity_suffix': '',
	}

	if ResponseType.THATS in response_types and state.just_used_til:
		flags['thats'] = True
	elif ResponseType.DIDNT_KNOW in response_types and state.just_used_til:
		flags['did_not_know'] = True
	else:
		flags['catch_all'] = True
	return flags