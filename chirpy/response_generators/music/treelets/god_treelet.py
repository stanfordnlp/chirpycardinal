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


class SymbolicTreelet(Treelet):
    def __init__(self, rg):
        super().__init__(rg)
        self.name = 'god_treelet'
        self.can_prompt = True
        supernodes = glob.glob('../**/response_generators/music/**/supernode.yaml', recursive=True)
        self.supernode_content = {}
        self.supernode_files = []
        for s in supernodes:
            supernode_name = s.split('/')[-2]
            self.supernode_files.append('/'.join(s.split('/')[:-1]))
            with open(s, "r") as stream:
                d = yaml.safe_load(stream)
                self.supernode_content[supernode_name] = d

        self.nlg_yamls = {}
        for path in self.supernode_files:
            node_name = path.split('/')[-1]
            if node_name == 'exit': continue
            nlg_yaml_file = os.path.join(path, 'nlg.yaml')
            with open(nlg_yaml_file, "r") as stream:
                d = yaml.safe_load(stream)
                self.nlg_yamls[node_name] = d['nlg']

    def get_trigger_response(self, **kwargs):
        # Triggered by KEYWORD_MUSIC
        logger.primary_info(f'{self.name} - Triggered')
        state, utterance, response_types = self.get_state_utterance_response_types()

        priority = self.rg._get_priority_from_answer_type()
        response = random.choice([
            'Music is one of my favorite things and I was wondering if we could talk about it.',
            'There\'s so much music here in the cloud and I\'m curious to know what you think about it.',
        ])
        return ResponseGeneratorResult(
            text=response, needs_prompt=False, cur_entity=None,
            priority=priority,
            state=state, conditional_state=ConditionalState(
                    prompt_treelet=self.name,
                    prev_supernode_str='music_introductory',
                    entering_music_rg=True
            ),
        )

    def get_next_supernode(self, state):
    	# DONT actually do it like this! Randomize next state selection!!
        for name in self.supernode_content:
            d = self.supernode_content[name]
            entry_reqs = d['requirements']
            for req_dict in entry_reqs:
                matches_entry_criteria = True
                for key in req_dict:
                    if state.__dict__[key] != req_dict[key]:
                        matches_entry_criteria = False
                        break
                if matches_entry_criteria:
                    return name
        return None

    def get_subnode(self, flags, supernode):
        subnode_nlgs = self.nlg_yamls[supernode]
        for nlg in subnode_nlgs:
            requirements = nlg['entry_conditions']
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
        # nlu = import_module('chirpy.response_generators.music.yaml_files.supernodes.music_handle_opinion.nlu')

        # NLU processing
        nlu = import_module(f'chirpy.response_generators.music.yaml_files.supernodes.{cur_supernode}.nlu')

        flags = nlu.nlu_processing(self.rg, state, utterance, response_types)

        # NLG processing
        subnode_name, nlg_response = self.get_subnode(flags, cur_supernode)

        context = get_context_for_supernode(self.name + '/' + cur_supernode)
        response = effify(nlg_response, global_context=context)

        # post-node state updates


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
            if state.have_prompted:
                return None
            if ResponseType.MUSIC_KEYWORD in response_types and \
               not ResponseType.POSITIVE in response_types:
                # If ResponseType.POSITIVE, we will prompt via HandleOpinionTreelet
                prompt_type = PromptType.CONTEXTUAL
                prompt_text = 'I love how you mentioned music! I\'ve been listening to a lot of new songs lately, and I\'d love to hear what you think.'
            else:
                prompt_type = PromptType.GENERIC
                prompt_text = 'By the way, I\'ve been listening to a lot of new songs lately, and I\'d love to hear what you think.'

            if conditional_state is None:
                conditional_state = ConditionalState(
                    prev_treelet_str=self.name,
                    next_treelet_str=self.name,
                    prev_supernode_str='music_introductory',
                    entering_music_rg=True
                )
            # next_treelet_str, question = self.get_next_treelet()
            return PromptResult(text=prompt_text, prompt_type=prompt_type, state=state, cur_entity=None,
                                conditional_state=conditional_state)

        prompt = self.supernode_content[cur_supernode]['prompt']
        prompt_text = ''
        for i in range(len(prompt)):
            case = prompt[i]
            requirements = case['required']
            matches_entry_criteria = True
            for key in requirements:
                if state.__dict__[key] != req_dict[key]:
                    matches_entry_criteria = False
                    break
            if matches_entry_criteria:
                prompt_text = case['prompt']
                break

        entity = self.rg.state_manager.current_state.entity_tracker.cur_entity

        # YAML processing for prompt treelet leading question
        return PromptResult(text=prompt_text, prompt_type=PromptType.CONTEXTUAL, state=state, cur_entity=entity,
                        conditional_state=conditional_state)

