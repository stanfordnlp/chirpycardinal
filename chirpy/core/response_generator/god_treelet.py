import logging
import random
import glob
import yaml
import os
from importlib import import_module

from chirpy.core.response_generator import Treelet, get_context_for_supernode
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator.state import NO_UPDATE
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType, AnswerType
from chirpy.core.response_generator.response_type import ResponseType

logger = logging.getLogger('chirpylogger')

def effify(non_f_str: str, global_context: dict):
    return eval(f'f"""{non_f_str}"""', global_context)

class GodTreelet(Treelet):
    def __init__(self, rg, rg_folder_name):
        super().__init__(rg)
        self.name = 'god_treelet'
        self.can_prompt = True

        self.state_module = import_module(f'chirpy.response_generators.{rg_folder_name}.state')

        supernodes = glob.glob(f'../**/response_generators/{rg_folder_name}/**/supernode.yaml', recursive=True)
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
            nlu = import_module(f'chirpy.response_generators.{rg_folder_name}.yaml_files.supernodes.{name}.nlu')
            self.nlu_libraries[name] = nlu

            # force all decorators to run by importing the nlg files, but we discard output
            if name != 'exit':
                dummy = import_module(f'chirpy.response_generators.{rg_folder_name}.yaml_files.supernodes.{name}.nlg_helpers')

        self.nlg_yamls = {}
        for path in self.supernode_files:
            node_name = path.split('/')[-1]
            if node_name == 'exit': continue
            nlg_yaml_file = os.path.join(path, 'nlg.yaml')
            with open(nlg_yaml_file, "r") as stream:
                d = yaml.safe_load(stream)
                self.nlg_yamls[node_name] = d

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
        for nlg in subnode_nlgs['response']:
            requirements = nlg['required_flags']
            matches_entry_criteria = True
            for key in requirements:
                if flags[key] != requirements[key]:
                    matches_entry_criteria = False
                    break
            if matches_entry_criteria:
                return nlg['node_name'], nlg['response']

        return None

    def get_unconditional_prompt_text(self, flags, supernode):
        for cases in self.nlg_yamls[supernode]['unconditional_prompt']:
            requirements = cases['required_flags']
            matches_entry_criteria = True
            for key in requirements:
                if flags[key] != requirements[key]:
                    matches_entry_criteria = False
                    break
            if matches_entry_criteria:
                return cases['case_name'], cases['prompt']
        return None

    def get_exposed_subnode_vars(self, supernode, subnode_name):
        subnode_nlgs = self.nlg_yamls[supernode]
        for nlg in subnode_nlgs['response']:
            if nlg['node_name'] == subnode_name:
                if 'expose_vars' not in nlg or nlg['expose_vars'] == 'None': return None
                return nlg['expose_vars']
        return None

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        logger.primary_info(f'{self.name} - Get response')
        state, utterance, response_types = self.get_state_utterance_response_types()
        needs_prompt = False
        # supernode_path = 'yaml_files/supernodes/'
        # cur_supernode = self.get_next_supernode(state)
        cur_supernode = state.cur_supernode
        if state.cur_supernode is None:
            # RG is being entered (introductory response)
            # Return empty string, but set state appropriately so prompt_treelet can take over
            # entity = self.rg.state_manager.current_state.entity_tracker.cur_entity
            state = self.rg.check_and_set_entry_conditions(state)
            cur_supernode = self.get_next_supernode(state)

        # NLU processing
        
        nlu = self.nlu_libraries[cur_supernode]
        flags = nlu.nlu_processing(self.rg, state, utterance, response_types)

        # NLG processing
        result = self.get_subnode(flags, cur_supernode)
        assert result is not None, f"There was no matching subnode in the supernode {cur_supernode} for the current state/utterance. Make sure the nlu covers all possible cases."
        subnode_name, nlg_response = result

        context = get_context_for_supernode(cur_supernode)
        cntxt = {
            'rg': self.rg,
            'state': state
        }
        context.update(cntxt)

        try:
            response = effify(nlg_response, global_context=context)
        except Exception as e:
            logger.error(e)
            logger.error(f'We had an NLG error in the supernode {cur_supernode} and subnode {subnode_name}. The problematic string inside the yaml file is "{nlg_response}". Check whether you have decorated the right functions!')
            raise

        print('*sentinel* god treelet response', response)

        # post-subnode state updates
        expose_vars = self.get_exposed_subnode_vars(cur_supernode, subnode_name)
        exposed_context = {}
        if expose_vars is not None:
            for key in expose_vars:
                exposed_context[key] = eval(expose_vars[key], context)

        context.update(exposed_context)
        subnode_state_updates = self.supernode_content[cur_supernode]['subnode_state_updates'][subnode_name]
        if subnode_state_updates == 'None': subnode_state_updates = {}
        global_post_state_updates = self.supernode_content[cur_supernode]['global_post_supernode_state_updates']
        if global_post_state_updates == 'None': global_post_state_updates = {}
        assert isinstance(subnode_state_updates, dict), f"subnode_state_updates of {subnode_name} in {cur_supernode} needs to be a dict or None"
        assert isinstance(global_post_state_updates, dict), f"global_post_state_updates of {subnode_name} in {cur_supernode} needs to be a dict or None"

        subnode_state_updates.update(global_post_state_updates)

        if 'priority' in subnode_state_updates:
            priority_context = dict(exposed_context)
            priority_context.update(globals())
            priority_context.update(cntxt)
            priority = eval(subnode_state_updates['priority'], priority_context)
            assert isinstance(priority, ResponsePriority)
            del subnode_state_updates['priority']
        if 'needs_prompt' in subnode_state_updates:
            needs_prompt = eval(str(subnode_state_updates['needs_prompt']), context)
            assert type(needs_prompt) == type(True) # make sure it is a boolean
            del subnode_state_updates['needs_prompt']
        else:
            needs_prompt = False

        if 'cur_entity' in subnode_state_updates:
            cur_entity = eval(subnode_state_updates['cur_entity'], context)
            assert cur_entity is None or isinstance(cur_entity, WikiEntity), f"error on {cur_entity}, eval string {subnode_state_updates['cur_entity']}"
            del subnode_state_updates['cur_entity']
        else:
            cur_entity = None

        if 'answer_type' in subnode_state_updates:
            answer_context = dict(exposed_context)
            answer_context.update(globals())
            answer_context.update(cntxt)
            answer_type = eval(subnode_state_updates['answer_type'], answer_context)
            assert isinstance(answer_type, AnswerType)
            del subnode_state_updates['answer_type']
        else:
            answer_type = AnswerType.NONE

        for key in subnode_state_updates:
            if type(subnode_state_updates[key]) != type(True):
                # eval non boolean flags
                subnode_state_updates[key] = eval(subnode_state_updates[key], context)
        subnode_state_updates['prompt_treelet'] = self.name
        subnode_state_updates['prev_treelet_str'] = self.name

        # YAML parse logic here
        return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=needs_prompt, state=state,
                                       cur_entity=cur_entity, answer_type=answer_type,
                                       conditional_state=self.state_module.ConditionalState(**subnode_state_updates))

    def get_prompt(self, conditional_state=None):
        state, utterance, response_types = self.get_state_utterance_response_types()

        if getattr(conditional_state, 'prompt_treelet', NO_UPDATE) == NO_UPDATE:
            # no prompt_treelet given. Respond with unconditional prompt
            prompting_supernodes = []
            for supernode_name in self.supernode_content:
                # ORDER MATTERS
                content = self.supernode_content[supernode_name]
                if 'unconditional_prompt_updates' in content:
                    prompting_supernodes.append((supernode_name, content['prompt_ranking']))

            prompt_supernodes_by_rank = sorted(prompting_supernodes, key = lambda x: x[1])
            for supernode_name, _ in prompt_supernodes_by_rank:
                nlu = self.nlu_libraries[supernode_name]
                flags = nlu.prompt_nlu_processing(self.rg, state, utterance, response_types)
                prompt_res = self.get_unconditional_prompt_text(flags, supernode_name)
                if prompt_res:
                    case_name, prompt_text = prompt_res

                    cntxt = get_context_for_supernode(supernode_name)
                    context = {
                        'rg': self.rg,
                        'state': state
                    }
                    context.update(cntxt)
                    context.update(globals())
                    
                    prompt_text = effify(prompt_text, context)
                    prompt_state_updates = self.supernode_content[supernode_name]['unconditional_prompt_updates'][case_name]
                    if prompt_state_updates == 'None': prompt_state_updates = {}
                    if 'prompt_type' in prompt_state_updates:
                        prompt_type = eval(str(prompt_state_updates['prompt_type']), context)
                        assert isinstance(prompt_type, PromptType)
                        del prompt_state_updates['prompt_type']
                    else:
                        prompt_type = PromptType.CONTEXTUAL

                    logger.info(f'chungus {prompt_text}')
                    return PromptResult(text=prompt_text, prompt_type=prompt_type, state=state, cur_entity=None,
                            conditional_state=self.state_module.ConditionalState(**prompt_state_updates))

            return None

        cur_supernode = self.get_next_supernode(conditional_state)
        if cur_supernode is None or conditional_state is None or cur_supernode == 'exit':
            # next_treelet_str, question = self.get_next_treelet()
            return None

        function_cache = get_context_for_supernode(cur_supernode)

        prompt_leading_questions = self.supernode_content[cur_supernode]['prompt_leading_questions']
        if prompt_leading_questions == 'None':
            prompt_leading_questions = []
        elif 'call_method' in prompt_leading_questions:
            method_name = prompt_leading_questions['call_method']
            if method_name not in function_cache:
                logger.error(f"Function {method_name} declared in yaml file not defined in function cache")
                raise KeyError(f'NLG helpers function cache error {method_name}')
            func = function_cache[method_name]
            conditional_state.cur_supernode = cur_supernode
            return func(self.rg, conditional_state)

        prompt_texts = []
        for i in range(len(prompt_leading_questions)):
            case = prompt_leading_questions[i]
            requirements = case['required']
            if requirements == 'None': requirements = {}
            assert isinstance(requirements, dict), f"requirements in prompt_leading_questions (supernode {cur_supernode}) needs to define a dict or None"
            matches_entry_criteria = True
            for key in requirements:
                if conditional_state.__dict__[key] != requirements[key]:
                    matches_entry_criteria = False
                    break
            if matches_entry_criteria:
                context = get_context_for_supernode(cur_supernode)
                cntxt = {
                    'rg': self.rg,
                    'state': conditional_state
                }
                context.update(cntxt)
                prompt_text = effify(case['prompt'], context)
                prompt_texts.append(prompt_text)

        entity = self.rg.state_manager.current_state.entity_tracker.cur_entity

        text = ''
        if len(prompt_texts) > 0:
            text = random.choice(prompt_texts)

        conditional_state.cur_supernode = cur_supernode
        prompt_type = PromptType.NO if text == '' else PromptType.CONTEXTUAL

        # YAML processing for prompt treelet leading question
        return PromptResult(text=text, prompt_type=prompt_type, state=state, cur_entity=entity,
                        conditional_state=conditional_state)

