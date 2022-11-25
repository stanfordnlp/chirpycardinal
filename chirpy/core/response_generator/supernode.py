import os
import yaml

from chirpy.core.callables import NamedCallable
from chirpy.core.state_manager import StateManager
from chirpy.core.regex import response_lists
from chirpy.core.response_generator.response_type import *
from chirpy.core.response_generator.neural_helpers import is_two_part, NEURAL_DECODE_CONFIG, get_random_fallback_neural_response
from chirpy.core.response_generator.state import NO_UPDATE, BaseState, BaseConditionalState
from chirpy.core.response_generator.neural_helpers import get_neural_fallback_handoff, neural_response_filtering
from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyResult, \
	emptyResult_with_conditional_state, emptyPrompt, UpdateEntity, AnswerType
from chirpy.core.response_generator.helpers import *
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.util import load_text_file, infl
from typing import Set, Optional, List, Dict
import logging
import os
import random

from importlib import import_module

from concurrent import futures

logger = logging.getLogger('chirpylogger')


# 		for cases in self.nlg_yamls[supernode]['unconditional_prompt']:
# 	requirements = cases['entry_conditions']
# 	matches_entry_criteria = True
# 	for key in requirements:
# 		if flags[key] != requirements[key]:
# 			matches_entry_criteria = False
# 			break
# 	if matches_entry_criteria:
# 		return cases['case_name'], cases['prompt']
# return None

CONDITION_STYLE_TO_BEHAVIOR = {
	'is_none': (lambda val: (val is None)),
	'is_true': (lambda val: (val is True)),
	'is_false': (lambda val: (val is False)),
	'is_value': (lambda val, target: (val == target)),
}

BASE_PATH = os.path.join(os.path.dirname(__file__), '../../symbolic_rgs')

def lookup_value(value_name, contexts):
	if '.' in value_name:
		assert len(value_name.split('.')) == 2, "Only one namespace allowed."
		namespace_name, value_name = value_name.split('.')
		value = contexts[namespace_name][value_name]
	else:
		assert False, f"Need a namespace for value name {value_name}."

def evaluate_nlg_call(data, python_context, contexts):
	if isinstance(data, str): # plain text
		return data
	
	assert isinstance(data, dict) and len(data) == 1, f"Failure: data is {data}"
	type = next(iter(data))
	nlg_params = data[type]
	if type == 'eval':
		assert isinstance(nlg_params, str)
		return effify(nlg_params, global_context=python_context)
	elif type == 'val':
		assert isinstance(nlg_params, str)
		return lookup_value(nlg_params, contexts)
	elif type == 'nlg_helper':
		assert isinstance(nlg_params, dict)
		function_name = nlg_params['name']
		assert function_name in python_context
		args = [rg] + data.get('args', [])   # Add RG as first argument
		return python_context[function_name](*args)
	elif type == 'inflect':
		assert isinstance(nlg_params, dict)
		inflect_token = nlg_params['inflect_token']
		inflect_val = lookup_value(nlg_params['inflect_entity'], contexts)
		return infl(inflect_token, inflect_val.is_plural())
	elif type == 'inflect_helper':
		assert isinstance(nlg_params, dict)
		inflect_function = nlg_params['type']
		inflect_input = evaluate_nlg_call(nlg_params['str'], python_context, contexts)
		return getattr(engine, inflect_function)(inflect_input)
	elif type == 'one of':
		return evaluate_nlg_call(random.choice(nlg_params), python_context, contexts)
	else:
		assert False, f"Generation type {type} not found!"
		
def evaluate_nlg_calls(datas, python_context, contexts):
	output = []
	if isinstance(datas, str):
		datas = [datas]
	for elem in datas:
		output.append(evaluate_nlg_call(elem, python_context, contexts))
	
	return ' '.join(output)

class Subnode:
	def __init__(self, data):
		logger.warning(f"Data is, {data}")
		self.data = data
		self.entry_conditions = data.get('entry_conditions', {})
		self.response = data.get('response')
		self.name = data['node_name']
		self.state_updates = data.get('state_updates', {})
		
	def is_valid(self, contexts):
		for condition_style, var_name in self.entry_conditions.items():
			assert condition_style in CONDITION_STYLE_TO_BEHAVIOR, f"Condition style {condition_style} is not recognized!"
			validity_func = CONDITION_STYLE_TO_BEHAVIOR[condition_style]
			evaluated_value = lookup_value(var_name, contexts)
			if not validity_func(evaluated_value): return False
		return True
		
	def get_response(self, python_context, contexts):
		return evaluate_nlg_calls(self.response, python_context, contexts)
		
	def get_state_updates(self):
		return self.state_updates
		
	def __str__(self):
		return f'Subnode({self.name})'

class Supernode:
	def __init__(self, name):
		self.yaml_path = os.path.join(BASE_PATH, name)
		with open(os.path.join(self.yaml_path, 'supernode.yaml'), 'r') as f:
			self.content = yaml.safe_load(f)
			
		self.requirements = self.load_requirements(self.content['supernode_requirements'])
		self.locals = self.content['locals']
		self.subnodes = self.load_subnodes(self.content['subnodes'])
		self.state_updates = self.content.get('set_state', {})
		self.prompt = self.content.get('prompt', [])
		self.name = name
		
		self.nlu = import_module(f'chirpy.symbolic_rgs.{name}.nlu')
		_ = import_module(f'chirpy.symbolic_rgs.{name}.nlg_helpers')		
	
	def load_requirements(self, requirements):
		self.requirements = requirements
		
	def is_eligible(self, state):
		return any(self.all_matches(self.requirement) in self.requirements)

	def get_global_subnodes(self):
		return []
		
	def load_subnodes(self, subnode_data):
		return [Subnode(data) for data in subnode_data]
	
	def get_optimal_subnode(self, contexts):
		possible_subnodes = [subnode for subnode in self.subnodes + self.get_global_subnodes() if subnode.is_valid(contexts)]
		assert len(possible_subnodes), "No subnode found!"
		
		# for now, just return the first possible subnode
		return possible_subnodes[0]
		
		return None
		
	def evaluate_locals(self, python_context, contexts):
		output = {}
		contexts['locals'] = output
		for local_key, local_values in self.locals.items():
			output[local_key] = evaluate_nlg_calls(local_values, python_context, contexts)
		return output
		
	def get_flags(self, rg, state, utterance):
		return self.nlu.nlu_processing(rg, state, utterance, set())
		
	def get_state_updates(self):
		return self.state_updates
		
	def get_prompt(self, python_context, contexts):
		return evaluate_nlg_calls(self.prompt, python_context, contexts)
		
	def __str__(self):
		return f"Supernode({self.yaml_path})"