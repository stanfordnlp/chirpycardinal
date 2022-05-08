import logging
import random
import glob
import yaml
from importlib import import_module

from chirpy.core.response_generator import Treelet
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType, AnswerType
from chirpy.response_generators.music.response_templates import handle_opinion_template
from chirpy.response_generators.music.music_helpers import ResponseType
from chirpy.response_generators.music.state import ConditionalState

logger = logging.getLogger('chirpylogger')


class GodTreelet(Treelet):
    def __init__(self, rg):
        super().__init__(rg)
        self.name = 'god_treelet'
        self.can_prompt = True
        supernodes = glob.glob('./**/supernode.yaml', recursive=True)
        self.supernode_content = {}
        for s in supernodes:
            supernode_name = s.split('/')[-2]
            self.supernode_files.append('/'.join(s.split('/')[:-1]))
            with open(s, "r") as stream:
                d = yaml.safe_load(stream)
                self.supernode_content[supernode_name] = d


    def get_trigger_response(self, **kwargs):
        # Triggered by KEYWORD_MUSIC
        logger.primary_info(f'{self.name} - Triggered')
        state, utterance, response_types = self.get_state_utterance_response_types()
        if ResponseType.YES in response_types:
            priority = ResponsePriority.CAN_START
            response = handle_opinion_template.HandleLikeMusicResponseTemplate().sample()
            # next_treelet_str, question = self.get_next_treelet()
            return ResponseGeneratorResult(
                text=response+question, needs_prompt=False, cur_entity=None,
                priority=priority,
                state=self.rg.state, conditional_state=ConditionalState(
                    prev_treelet_str=self.name,
                    next_treelet_str=self.name,
                    prev_supernode_str='music_introductory',
                    entering_music_rg=True
                ),
                answer_type=AnswerType.QUESTION_SELFHANDLING
            )

    def get_next_supernode(self, state):
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
                    return name
        return None

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        logger.primary_info(f'{self.name} - Get response')
        state, utterance, response_types = self.get_state_utterance_response_types()
        needs_prompt = False
        # supernode_path = 'yaml_files/supernodes/'
        cur_supernode = self.get_next_supernode(state)
        mod = import_module('chirpy.response_generators.music.yaml_files.supernodes.music_handle_opinion.nlu')



        # YAML parse logic here
        return ResponseGeneratorResult(text='chungus', priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False, state=state,
                                       cur_entity=None,
                                       conditional_state=None,
                                       answer_type=AnswerType.QUESTION_SELFHANDLING)

    def get_prompt(self, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()
        cur_supernode = self.get_next_supernode(state)
        mod = import_module('chirpy.response_generators.music.yaml_files.supernodes.music_handle_opinion.nlu')
        # print('chungus', dir(mod))
        print('chungus', cur_supernode)
        if cur_supernode is None:
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
            # next_treelet_str, question = self.get_next_treelet()
            return PromptResult(text=prompt_text, prompt_type=prompt_type, state=state, cur_entity=None,
                                conditional_state=ConditionalState(
                                    have_prompted=True,
                                    prev_treelet_str=self.name,
                                    next_treelet_str=self.name,
                                ))

        prompt_leading_questions = self.supernode_content[cur_supernode]['prompt_leading_questions']
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
                prompt_text = case['prompt']
                break

        entity = self.rg.state_manager.current_state.entity_tracker.cur_entity

        # YAML processing for prompt treelet leading question
        return PromptResult(text=prompt_text, prompt_type=PromptType.CONTEXTUAL, state=state, cur_entity=entity,
                        conditional_state=ConditionalState())

