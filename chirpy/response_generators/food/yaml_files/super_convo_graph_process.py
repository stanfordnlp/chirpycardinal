from collections import defaultdict
import yaml
import networkx as nx
import matplotlib.pyplot as plt
import sys
import os
import ast

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

def powerset(s):
    x = len(s)
    masks = [1 << i for i in range(x)]
    for i in range(1 << x):
        yield [ss for mask, ss in zip(masks, s) if i & mask]

def parse_all_exit_states(entry_conditions, set_state_on_finish, possible_state_updates):
	exit_state = entry_conditions.copy()
	if set_state_on_finish == 'None':
		set_state_on_finish = dict()
	for key in set_state_on_finish:
		exit_state[key] = set_state_on_finish[key]

	all_possible_exit_states = []

	subset = powerset(possible_state_updates)
	for upds in subset:
		this_state = exit_state.copy()
		for u in upds:
			key = list(u.keys())[0]
			this_state[key] = u[key]
		all_possible_exit_states.append(this_state)

	return all_possible_exit_states

def check_correct_yaml_format(d, yaml_file):
	assert 'name' in d, f'{yaml_file} needs to define a name field'
	assert 'global_state_entry_requirements' in d, f'{yaml_file} needs to define a global_state_entry_requirements field'
	assert 'subnode_state_updates' in d, f'{yaml_file} needs to define a subnode_state_updates field'
	assert 'prompt_leading_questions' in d, f'{yaml_file} needs to define a prompt_leading_questions field'
	assert 'required_exposed_variables' in d, f'{yaml_file} needs to define a required_exposed_variables field'

def check_global_entry_reqs_are_booleans(d):
	global_reqs = d['global_state_entry_requirements']
	for entry_reqs in global_reqs:
		for key in entry_reqs:
			val = entry_reqs[key]
			assert type(val) == type(True), f"key,val pair {key},{val} in {d['name']}'s global entry reqs needs to be boolean flags"

def check_prompt_leading_questions_reqs_are_booleans(d):
	prompt_leading_questions = d['prompt_leading_questions']
	if prompt_leading_questions == 'None' or 'call_method' in prompt_leading_questions:
		return
	for case in prompt_leading_questions:
		assert 'required' in case
		assert 'prompt' in case
		for key in case['required']:
			val = entry_reqs[key]
			assert type(val) == type(True), f"key,val pair {key},{val} in {d['name']}'s prompt_leading_questions reqs needs to be boolean flags"

class TreeletNode:
	def __init__(self, yaml_file):
		self.path = yaml_file
		with open(yaml_file, "r") as stream:
			d = yaml.safe_load(stream)
			self.name = d['name']

			# --- Formatting checks -----
			check_correct_yaml_format(d, yaml_file)
			check_global_entry_reqs_are_booleans(d)
			check_prompt_leading_questions_reqs_are_booleans(d)
			# ----------------------

			self.all_possible_entry = []
			self.all_possible_exit_states = []
			self.subnode_names = set()

			self.req_exposed_vars = set()
			for var in d['required_exposed_variables']:
				self.req_exposed_vars.add(var)

			global_entry_requirements = d['global_state_entry_requirements']
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
parser.set_defaults(draw_graph=False)

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
if is_cylic:
	print('ERROR: Treelet/Supernode Graph is cyclic. Fix yaml files')
	print(G)
	sys.exit(1)

print('Treelet graph', G)
print('--------')
print()

paths = find_all_paths(find_all_parents(G, f'{args.intro_node} '), f'{args.intro_node} ', 'exit ')

print('number of unique convo paths between {} and exit: {}'.format(args.intro_node, len(paths)))
print('---- List of unique paths --------')
for p in paths:
	print(p)
print('-----------')
input("Convo Graph checks complete. Press Enter to continue static checker...\n")

draw_graph = args.draw_graph
if draw_graph:
	nx_G = nx.DiGraph()
	print('Displaying Graph... Make sure to close popup to continue rest of static checks.')
	for key in G:
		for child in G[key]:
			nx_G.add_edge(key[:-1], child[:-1])
	nx.draw(nx_G, with_labels = True, node_size=800)
	plt.show()



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
nlu_files = glob.glob(os.path.join(args.path, '**/nlu.py'), recursive=True)
assert len(nodes) >= len(nlu_files) - 1, 'all supernodes except for exit must define an nlu.py file'
for nlu in nlu_files:
	if '/exit/' in nlu: continue # ignore exit supernode
	file_content = None
	with open(nlu, 'r') as f:
		file_content = f.read()
	a = ast.parse(file_content)
	definitions = [n for n in ast.walk(a) if type(n) == ast.FunctionDef]
	found_nlu_processing = False
	for d in definitions:
		if d.name == 'nlu_processing':
	 		found_nlu_processing = True
	 		args = d.args.args
	 		assert len(args) == 4, f'{nlu} must define the method nlu_processing with the four args: rg, state, utterance, response_types'

	assert found_nlu_processing, f"method nlu_processing not found in file {nlu} and must be defined"

input("nlu.py checks complete. Press Enter to continue static checker...\n")

# Verify that all subnodes defined in supernode.yaml exist in nlg.yaml
# Verify that variables that need to be exposed are actually exposed in nlg.yaml
print('Checking nlg.yaml files...')
for n in nodes:
	if n.name == 'exit': continue
	head_path = os.path.dirname(n.path)
	nlg_path = os.path.join(head_path, 'nlg.yaml')
	with open(nlg_path, "r") as stream:
		nlg_yaml = yaml.safe_load(stream)
	subnode_names = set()
	for subnode in nlg_yaml:
		assert 'node_name' in subnode, f'all subnodes in {n.name} must define a node_name field'
		sub_name = subnode['node_name']
		assert 'required_flags' in subnode, f'{sub_name} subnode in {n.name} must define a required_flags field'
		assert 'response' in subnode, f'{sub_name} subnode in {n.name} must define a response field'
		assert 'expose_vars' in subnode, f'{sub_name} subnode in {n.name} must define a expose_vars field'

		exposed_vars = set()
		for var in subnode['expose_vars']:
			exposed_vars.add(var)

		assert n.req_exposed_vars.issubset(exposed_vars), f'{sub_name} must expose the required variables specified by {n.path}'

		subnode_names.add(sub_name)
	assert subnode_names == n.subnode_names, f'The subnodes defined in {n.path} must exactly equal the defined subnodes in the corresponding nlg.yaml file'

input("nlg yaml checks complete. Press Enter to continue static checker...\n")

print('static checker COMPLETED.')
# Ensure prompt leading q requirements are always boolean flags (like global state reqs)