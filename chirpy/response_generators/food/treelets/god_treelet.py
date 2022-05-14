import logging
import random
import glob
import yaml
import os
from importlib import import_module
# from typing import Any

from chirpy.core.response_generator import Treelet, get_context_for_supernode
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType, AnswerType
from chirpy.response_generators.music.response_templates import handle_opinion_template
from chirpy.response_generators.music.music_helpers import ResponseType
from chirpy.response_generators.music.state import ConditionalState

logger = logging.getLogger('chirpylogger')

def effify(non_f_str: str, global_context: dict):
    return eval(f'f"""{non_f_str}"""', global_context)


class GodTreelet(Treelet):
    def __init__(self, rg):
        super().__init__(rg)
        self.name = 'god_treelet'
        self.can_prompt = True
        supernodes = glob.glob('../**/response_generators/food/**/supernode.yaml', recursive=True)
        self.supernode_content = {}
        self.supernode_files = []
        for s in supernodes:
            supernode_name = s.split('/')[-2]
            self.supernode_files.append('/'.join(s.split('/')[:-1]))
            with open(s, "r") as stream:
                d = yaml.safe_load(stream)
                self.supernode_content[supernode_name] = d

        self.nlu_libraries = {}
        for name in self.supernode_content:
        	nlu = import_module(f'chirpy.response_generators.food.yaml_files.supernodes.{name}.nlu')
        	self.nlu_libraries[name] = nlu

        self.nlg_yamls = {}
        for path in self.supernode_files:
            node_name = path.split('/')[-1]
            if node_name == 'exit': continue
            nlg_yaml_file = os.path.join(path, 'nlg.yaml')
            with open(nlg_yaml_file, "r") as stream:
                d = yaml.safe_load(stream)
                self.nlg_yamls[node_name] = d['nlg']

    def get_next_supernode(self, state):
    	# Get matching next supernodes and return one sampled at random
    	matching_supernodes = []
        for name in self.supernode_content:
            d = self.supernode_content[name]
            entry_reqs = d['global_state_entry_requirements']
            for req_dict in entry_reqs:
                matches_entry_criteria = True
                for key in req_dict:
                    if state.__dict__[key] != req_dict[key]:
                        matches_entry_criteria = False
                        break

                if matches_entry_criteria:
                    matching_supernodes.append(name)
                    break

        if len(matching_supernodes) == 0: return None
        return random.choice(matching_supernodes)

    def get_subnode(self, flags, supernode):
        subnode_nlgs = self.nlg_yamls[supernode]
        for nlg in subnode_nlgs:
            requirements = nlg['required_flags']
            matches_entry_criteria = True
            for key in requirements:
                if flags[key] != requirements[key]:
                    matches_entry_criteria = False
                    break
            if matches_entry_criteria:
                return nlg['node_name'], nlg['response']
        return None

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        logger.primary_info(f'{self.name} - Get response')
        state, utterance, response_types = self.get_state_utterance_response_types()
        needs_prompt = False
        # supernode_path = 'yaml_files/supernodes/'
        cur_supernode = self.get_next_supernode(state)
        if cur_supernode is None:
        	# RG is being entered (introductory response)
        	# Return empty string, but set state appropriately so prompt_treelet can take over
        	entity = self.rg.state_manager.current_state.entity_tracker.cur_entity
        	if entity.name == 'Food':
        		return ResponseGeneratorResult(text='', priority=priority, needs_prompt=False, state=state,
                                       cur_entity=None,
                                       conditional_state=ConditionalState(
                                           prompt_treelet=self.name,
                                           cur_entity_is_food=True))
        	elif is_known_food(entity.name.lower()):
        		return ResponseGeneratorResult(text='', priority=priority, needs_prompt=False, state=state,
                                       cur_entity=None,
                                       conditional_state=ConditionalState(
                                           prompt_treelet=self.name,
                                           cur_entity_known_food=True))

        	return ResponseGeneratorResult(text='', priority=priority, needs_prompt=True, state=state,
                                       cur_entity=None,
                                       conditional_state=ConditionalState())


        # NLU processing
        
        nlu = self.nlu_libraries[cur_supernode]
        flags = nlu.nlu_processing(self.rg, state, utterance, response_types)

        # NLG processing
        subnode_name, nlg_response = self.get_subnode(flags, cur_supernode)

        context = get_context_for_supernode(self.name + '/' + cur_supernode)
        response = effify(nlg_response, global_context=context)

        # post-node state updates (maybe do this in prompt treelet?)


        # YAML parse logic here
        return ResponseGeneratorResult(text='chungus', priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False, state=state,
                                       cur_entity=None,
                                       conditional_state=ConditionalState(
                                           prev_treelet_str=self.name,
                                           prompt_treelet=self.name),
                                       answer_type=AnswerType.QUESTION_SELFHANDLING)

    def get_prompt(self, conditional_state=None):
        state, utterance, response_types = self.get_state_utterance_response_types()
        cur_supernode = self.get_next_supernode(state)
        # print('chungus', dir(mod))
        if cur_supernode is None or conditional_state is None:
            # next_treelet_str, question = self.get_next_treelet()
            return None

        function_cache = get_context_for_supernode(supernode)

        prompt_leading_questions = self.supernode_content[cur_supernode]['prompt_leading_questions']
        if prompt_leading_questions == 'None':
        	prompt_leading_questions = []
    	elif 'call_method' in prompt_leading_questions:
    		method_name = prompt_leading_questions['call_method']
    		if method_name not in function_cache:
    			logger.error(f"Function {method_name} declared in yaml file not defined in function cache")
    			raise KeyError(f'NLG helpers function cache error {method_name}')
    		func = function_cache[method]
    		return func(self.rg, conditional_state)

        prompt_text = ''
        for i in range(len(prompt_leading_questions)):
            case = prompt_leading_questions[i]
            requirements = case['required']
            matches_entry_criteria = True
            for key in requirements:
                if state.__dict__[key] != req_dict[key]:
                    matches_entry_criteria = False
                    break
            if matches_entry_criteria:
            	cntxt = {
            		'rg': self.rg,
            		'state': state
            	}
                prompt_text = effify(case['prompt'], cntxt)
                break

        entity = self.rg.state_manager.current_state.entity_tracker.cur_entity

        # YAML processing for prompt treelet leading question
        return PromptResult(text=prompt_text, prompt_type=PromptType.CONTEXTUAL, state=state, cur_entity=entity,
                        conditional_state=conditional_state)

