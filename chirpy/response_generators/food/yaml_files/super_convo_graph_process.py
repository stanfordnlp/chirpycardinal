from collections import defaultdict
import yaml
import networkx as nx
import matplotlib.pyplot as plt
import sys
import os
import ast
import py_compile
import tempfile

# modified BFS
def find_all_parents(G, s):
	Q = [s]
	parents = defaultdict(set)
	while len(Q) != 0:
		v = Q[0]
		Q.pop(0)
		for w in G.get(v, []):
			parents[w].add(v)
			Q.append(w)
	return parents

def cyclic(g):
	"""Return True if the directed graph g has a cycle.
	g must be represented as a dictionary mapping vertices to
	iterables of neighbouring vertices. For example:

	>>> cyclic({1: (2,), 2: (3,), 3: (1,)})
	True
	>>> cyclic({1: (2,), 2: (3,), 3: (4,)})
	False

	"""
	path = set()
	visited = set()

	def visit(vertex):
		if vertex in visited:
			return False
		visited.add(vertex)
		path.add(vertex)
		for neighbour in g.get(vertex, ()):
			if neighbour in path or visit(neighbour):
				return True
		path.remove(vertex)
		return False

	return any(visit(v) for v in g)

# recursive path-finding function (assumes that there exists a path in G from a to b)   
def find_all_paths(parents, a, b):
	return [a] if a == b else [y + b for x in list(parents[b]) for y in find_all_paths(parents, a, x)]

def count_with_self_loops(paths, self_loops):
	cycle_num_paths = 0
	for i in range(len(paths)):
		path = paths[i].split()
		num_self_loops = 0
		for p in path:
			if p in self_loops:
				num_self_loops += 1
		cycle_num_paths += (2 ** num_self_loops)
	return cycle_num_paths

def topological_sort_grouped(G):
	indegree_map = {v: d for v, d in G.in_degree() if d > 0}
	zero_indegree = [v for v, d in G.in_degree() if d == 0]
	while zero_indegree:
		yield zero_indegree
		new_zero_indegree = []
		for v in zero_indegree:
			for _, child in G.edges(v):
				indegree_map[child] -= 1
				if not indegree_map[child]:
					new_zero_indegree.append(child)
		zero_indegree = new_zero_indegree

def powerset(s):
	x = len(s)
	masks = [1 << i for i in range(x)]
	for i in range(1 << x):
		yield [ss for mask, ss in zip(masks, s) if i & mask]

def check_correct_yaml_format(d, yaml_file):
	assert 'name' in d, f'{yaml_file} needs to define a name field'
	assert 'requirements' in d, f'{yaml_file} needs to define a requirements field'
	assert 'subnode_state_updates' in d, f'{yaml_file} needs to define a subnode_state_updates field'
	assert 'prompt' in d, f'{yaml_file} needs to define a prompt field'
	# assert 'required_exposed_variables' in d, f'{yaml_file} needs to define a required_exposed_variables field'

def check_global_entry_reqs_are_booleans(d):
	global_reqs = d['requirements']
	assert isinstance(global_reqs, list), f"global reqs in supernode {d['name']} must be a list of non-trivial conditions"
	for entry_reqs in global_reqs:
		for key in entry_reqs:
			val = entry_reqs[key]
			assert type(val) == type(True), f"key,val pair {key},{val} in {d['name']}'s global entry reqs needs to be boolean flags"

def check_prompt_reqs_are_booleans(d):
	prompt = d['prompt']
	if prompt == 'None' or 'call_method' in prompt:
		return
	for case in prompt:
		assert 'required' in case
		assert 'prompt' in case
		cases = {} if case['required'] == 'None' else case['required']
		for key in cases:
			val = cases[key]
			assert type(val) == type(True), f"key,val pair {key},{val} in {d['name']}'s prompt reqs needs to be boolean flags"

def check_unconditional_prompt(d):
	assert ('prompt_ranking' in d and 'unconditional_prompt_updates' in d) \
	 or ('prompt_ranking' not in d and 'unconditional_prompt_updates' not in d), \
	 f"if supernode {d['name']} defines an unconditional prompt, it must have the requisite yaml keys, otherwise it shouldn't have these keys"

	if 'prompt_ranking' not in d:
		return False

	assert isinstance(d['prompt_ranking'], int), f"supernode {d['name']} needs to define an integer prompt_ranking"

	for case in d['unconditional_prompt_updates']:
		val = d['unconditional_prompt_updates'][case]
		assert isinstance(val, dict) or val == 'None', f"Each case of prompt updates in supernode {d['name']} should be a dict or None"
	return True


class TreeletNode:
	def __init__(self, yaml_file):
		self.path = yaml_file
		with open(yaml_file, "r") as stream:
			d = yaml.safe_load(stream)
			self.name = d['name']
			self.decorated_functions = {}

			# --- Formatting checks -----
			check_correct_yaml_format(d, yaml_file)
			check_global_entry_reqs_are_booleans(d)
			check_prompt_reqs_are_booleans(d)
			self.has_unconditional_prompt = check_unconditional_prompt(d)
			# ----------------------

			if self.has_unconditional_prompt:
				self.prompt_case_names = set()
				for case in d['unconditional_prompt_updates']:
					self.prompt_case_names.add(case)
				self.prompt_ranking = d['prompt_ranking']

			self.all_possible_entry = []
			self.all_possible_exit_states = []
			self.subnode_names = set()

			self.req_exposed_vars = set()
			if 'required_exposed_variables' in d and d['required_exposed_variables'] != 'None':
				self.exposing_vars = True
				for var in d['required_exposed_variables']:
					self.req_exposed_vars.add(var)
			else:
				self.exposing_vars = False

			global_entry_requirements = d['requirements']
			for e in global_entry_requirements:
				self.all_possible_entry.append(e)
				subnode_state_updates = d['subnode_state_updates']
				for subnode in subnode_state_updates:
					self.subnode_names.add(subnode)
					exit_state = e.copy()
					exit_actions = subnode_state_updates[subnode]
					if exit_actions == 'None':
						exit_actions = {}
					for key in exit_actions:
						exit_state[key] = exit_actions[key]
					global_post_supernode_state_updates = {}
					if d['global_post_supernode_state_updates'] != 'None':
						global_post_supernode_state_updates = d['global_post_supernode_state_updates']
					for key in global_post_supernode_state_updates:
						exit_state[key] = global_post_supernode_state_updates[key]
					self.all_possible_exit_states.append(exit_state)

	def does_edge_exist(self, second_node):
		# treat self as src, second_node as dst
		exit_conds = self.all_possible_exit_states
		entry_conds = second_node.all_possible_entry
		for i in entry_conds:
			for e in exit_conds:
				equal = True
				for key in i:
					if key not in e:
						if type(i[key]) == type(True) and i[key] == True:
							equal = False
						elif type(i[key]) != type(True) and i[key] != 'None': 
							equal = False
					elif i[key] != e[key]:
						equal = False
				if equal:
					return True

		return False

import glob
import argparse
parser = argparse.ArgumentParser()

parser.add_argument('--path', help='path to folder of supernodes', default='./supernodes')
parser.add_argument('--intro_node', help='name of supernode to treat as RG entry point', required=True)
parser.add_argument('--draw_graph', action='store_true')
parser.add_argument('--ignore_cycles', action='store_true')
parser.set_defaults(draw_graph=False)
parser.set_defaults(ignore_cycles=False)


args = parser.parse_args()

assert os.path.isdir(args.path), '--path must be a valid path to a directory'
assert os.path.basename(args.path) == 'supernodes', '--path directory must be named supernodes'

print('Building & Checking Conversational Graph...')
treelet_node_files = glob.glob(os.path.join(args.path, '**/supernode.yaml'), recursive=True)
nodes = []
for f in treelet_node_files:
	n = TreeletNode(f)
	assert n.name == os.path.basename(os.path.dirname(f)), f'{f} should define the supernode name to be equal to the name of its enclosing folder'
	nodes.append(n)

G = {}

# verify that a node contains and intro & exit node - DONE
assert any([n.name == 'exit' for n in nodes]), 'make sure a supernode titled exit exists'
assert any([n.name == args.intro_node for n in nodes]), 'make sure the specified intro_node exists as a supernode'

for i in range(len(nodes)):
	for j in range(len(nodes)):
		# if i == j: continue
		src = nodes[i]
		dst = nodes[j]
		if src.does_edge_exist(dst):
			if src.name + ' ' not in G:
				G[src.name + ' '] = [dst.name + ' ']
			else:
				G[src.name + ' '].append(dst.name + ' ')

del G['exit ']

is_cylic = cyclic(G)
if is_cylic and not args.ignore_cycles:
	print('ERROR: Treelet/Supernode Graph is cyclic. Fix yaml files. You should try to add/split supernodes until the graph is not cyclic.')
	print(G)
	sys.exit(1)

print('Treelet graph', G)
print('--------')
print()

input('Press enter to continue...\n')

if not args.ignore_cycles:
	# only run path finding if the convo graph is supposed to not have cycles
	paths = find_all_paths(find_all_parents(G, f'{args.intro_node} '), f'{args.intro_node} ', 'exit ')

	print('number of unique convo paths between {} and exit: {}'.format(args.intro_node, len(paths)))
	print('---- List of unique paths --------')
	for p in paths:
		print(p)
	print('-----------')
	input("Convo Graph checks complete. Press Enter to continue static checker...\n")

draw_graph = args.draw_graph
if draw_graph:
	temp_G = nx.DiGraph()
	print('Displaying Graph... Make sure to close popup to continue rest of static checks.')
	for key in G:
		for child in G[key]:
			temp_G.add_edge(key[:-1], child[:-1])

	if args.ignore_cycles:
		# assume we cannot topological sort
		nx_G = temp_G
	else:
		hierarchy = list(topological_sort_grouped(temp_G))

		nx_G = nx.DiGraph()
		for i in range(len(hierarchy)):
			level = hierarchy[i]
			for node in level:
				nx_G.add_node(node, level=i+1)

		for key in G:
			for child in G[key]:
				nx_G.add_edge(key[:-1], child[:-1])

	pos = nx.nx_pydot.graphviz_layout(nx_G, prog="dot")
	nx.draw(nx_G, pos=pos, with_labels=True, node_size=800, font_weight='bold')
	plt.show()
	# nx.draw(nx_G, with_labels = True, node_size=800)
	# plt.show()
	# Can i enforce topological ordering
	# 



# Verify every state access exists in initial state
print('Assessing declared state variables...')

state_vals = set()
for n in nodes:
	for d in n.all_possible_entry:
		for key in d:
			state_vals.add(key)
	for d in n.all_possible_exit_states:
		for key in d:
			state_vals.add(key)

state_vals.discard('priority')
state_vals.discard('needs_prompt')
state_vals.discard('cur_entity')
state_vals = list(state_vals)
state_vals.sort()
print('The following state variables were found: (MAKE SURE THESE ARE DEFINED IN state.py, otherwise errors will occur)')
for t in state_vals:
	print(t)
print('---------')
input("Press Enter to continue static checker...\n")

# check that nlu.py defines method nlu_processing
print('Checking nlu.pu files...')
for n in nodes:
	if n.name == 'exit': continue
	head_path = os.path.dirname(n.path)
	nlu = os.path.join(head_path, 'nlu.py')
	assert os.path.exists(nlu), f"check {n.name}; all supernodes except exit must define nlu.py"

	file_content = None
	with open(nlu, 'r') as f:
		file_content = f.read()
	a = ast.parse(file_content)

	definitions = [n for n in ast.walk(a) if type(n) == ast.FunctionDef]

	found_nlu_processing = False
	found_prompt_nlu_processing = False
	for d in definitions:
		if d.name == 'nlu_processing':
			found_nlu_processing = True
			args = d.args.args
			assert len(args) == 4, f'{nlu} must define the method nlu_processing with the four args: rg, state, utterance, response_types'
		elif d.name == 'prompt_nlu_processing' and n.has_unconditional_prompt:
			found_prompt_nlu_processing = True
			args = d.args.args
			assert len(args) == 4, f'{nlu} must define the method prompt_nlu_processing with the four args: rg, state, utterance, response_types'

	assert found_nlu_processing, f"method nlu_processing not found in file {nlu} and must be defined"
	assert found_prompt_nlu_processing if n.has_unconditional_prompt else True, f"{n.name} is a supernode with unconditional prompt, so its nlu.py file must define a prompt_nlu_processing method"

input("nlu.py checks complete. Press Enter to continue static checker and find major linter errors in nlu.py files ...\n")
print('Running (please be patient)...\n')
for n in nodes:
	if n.name == 'exit': continue
	head_path = os.path.dirname(n.path)
	nlu = os.path.join(head_path, 'nlu.py')
	os.system(f'pylint --errors-only --disable=import-error {nlu}')

input("nlu.py ERROR-only (no style checks, etc.) linter checks complete. Fix any error msgs printed above. Press Enter to continue static checker...\n")

print('Checking for syntax errors in nlg_helpers.py files...')
for n in nodes:
	if n.name == 'exit': continue
	head_path = os.path.dirname(n.path)
	nlg_path = os.path.join(head_path, 'nlg_helpers.py')
	if not os.path.exists(nlg_path): continue
	# run pylint as well
	try:
		py_compile.compile(f'{nlg_path}', doraise=True)
	except py_compile.PyCompileError as e:
		raise Exception(f"Syntax error detected in {nlg_path}. Fix error given in PyCompileError msg above.") from e

	file_content = None
	with open(nlg_path, 'r') as f:
		file_content = f.read()

	a = ast.parse(file_content)
	definitions = [n for n in ast.walk(a) if type(n) == ast.FunctionDef]
	for d in definitions:
		for dec in d.decorator_list:
			if 'id' in dec.__dict__ and dec.id == 'nlg_helper':
				# d is decorated with nlg_helper
				n.decorated_functions[d.name] = d

	# pylint --errors-only --disable=import-error music_response_generator.py
	os.system(f'pylint --errors-only --disable=import-error {nlg_path}')


input("nlg_helpers.py checks complete. Fix any linter errors raised above. Press Enter to continue static checker...\n")
# Verify that all subnodes defined in supernode.yaml exist in nlg.yaml
# Verify that variables that need to be exposed are actually exposed in nlg.yaml
print('Checking nlg.yaml files...')
for n in nodes:
	if n.name == 'exit': continue
	head_path = os.path.dirname(n.path)
	nlg_path = os.path.join(head_path, 'nlg.yaml')
	assert os.path.exists(nlg_path), f"check {n.name}; all supernodes except exit must define nlg.yaml"
	with open(nlg_path, "r") as stream:
		nlg_yaml = yaml.safe_load(stream)
	subnode_names = set()
	assert 'response' in nlg_yaml, f"{nlg_path} must define a response field to store subnode responses"

	for subnode in nlg_yaml['response']:
		assert 'node_name' in subnode, f'all subnodes in {n.name} must define a node_name field'
		sub_name = subnode['node_name']
		assert 'entry_conditions' in subnode, f'{sub_name} subnode in {n.name} must define a entry_conditions field'
		assert 'response' in subnode, f'{sub_name} subnode in {n.name} must define a response field'
		non_f_string = subnode['response']

		# Check syntax/formatting errors in all nlg response format strings:
		a = f"f\"\"\"{non_f_string}\"\"\""

		try:
			parsed = ast.parse(a)
			funcs = [n for n in ast.walk(parsed) if type(n) == ast.Call]
		except Exception as e:
			raise Exception(f"Format error detected in f-string response of subnode {sub_name} inside {nlg_path}. Fix f-string syntax error given in the error msg above") from e

		for f in funcs:
			if 'id' in f.func.__dict__:
				# make sure that this func is decorated
				assert f.func.id in n.decorated_functions, f"detected function {f.func.id} in f-string response of subnode {sub_name} inside supernode {n.name} that was not decorated with @nlg_helper."
				num_defaults = len(n.decorated_functions[f.func.id].args.defaults)
				num_total_args = len(n.decorated_functions[f.func.id].args.args)

				assert len(f.args) <= num_total_args and len(f.args) >= num_total_args - num_defaults, f"function {f.func.id} in f-string response of subnode {sub_name} inside supernode {n.name} not called with correct num args."

		if 'expose_vars' in subnode:
			assert n.exposing_vars, f"supernode.yaml for {n.name} must define required_exposed_variables if subnode declares 'expose_vars'"
		if n.exposing_vars:
			assert 'expose_vars' in subnode, f'{sub_name} subnode in {n.name} must define a expose_vars field'

			exposed_vars = set()
			for var in subnode['expose_vars']:
				exposed_vars.add(var)

			assert n.req_exposed_vars.issubset(exposed_vars), f'{sub_name} must expose the required variables specified by {n.path}'

		subnode_names.add(sub_name)
	assert subnode_names == n.subnode_names, f'The subnodes defined in {n.path} must exactly equal the defined subnodes in the corresponding nlg.yaml file'

	if n.has_unconditional_prompt:
		# if supernode.yaml defines unconditional stuff, nlg.yaml must also match

		# NEED SYNTAX CHECKS!!		
		assert 'unconditional_prompt' in nlg_yaml, f"{nlg_path} must define a unconditional_prompt field"
		prompt_case_names = set()
		for case in nlg_yaml['unconditional_prompt']:
			assert 'case_name' in case and 'entry_conditions' in case and 'prompt' in case, f"make sure {nlg_path} has required categories defined in unconditional_prompt"
			prompt_case_names.add(case['case_name'])

			prompt_text = case['prompt']
			a = f"f\"\"\"{prompt_text}\"\"\""

			try:
				parsed = ast.parse(a)
				funcs = [n for n in ast.walk(parsed) if type(n) == ast.Call]
			except Exception as e:
				print(prompt_text)
				raise Exception(f"Format error detected in f-string prompt of case {case['case_name']} inside {nlg_path}. Fix f-string syntax error given in the error msg above") from e

			for f in funcs:
				if 'id' in f.func.__dict__:
					# make sure that this func is decorated
					assert f.func.id in n.decorated_functions, f"detected function {f.func.id} in f-string prompt of prompt case {case['case_name']} inside supernode {n.name} that was not decorated with @nlg_helper."
					num_defaults = len(n.decorated_functions[f.func.id].args.defaults)
					num_total_args = len(n.decorated_functions[f.func.id].args.args)

					assert len(f.args) <= num_total_args and len(f.args) >= num_total_args - num_defaults, f"function {f.func.id} in f-string response of prompt case {case['case_name']} inside supernode {n.name} not called with correct num args."


		assert n.prompt_case_names == prompt_case_names, f"{n.name} supernode must define the exact same unconditional prompt case names as in the nlg.yaml file"

input("nlg yaml checks complete. Press Enter to continue static checker...\n")

print('static checker COMPLETED.')

# Need syntax checks on nlg responses in nlg.yaml - use ast.parse to check syntax + func decorations
# or something like python -m py_compile nlg_helpers.py

# DO CHECKS FOR NLG.YAML prompt responses!!
