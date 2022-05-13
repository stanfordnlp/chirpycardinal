from collections import defaultdict
import yaml
import networkx as nx
import matplotlib.pyplot as plt
import sys

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

class TreeletNode:
	def __init__(self, yaml_file):
		with open(yaml_file, "r") as stream:
			d = yaml.safe_load(stream)
			self.name = d['name']
			# self.trigger_response = d['trigger_response']
			self.all_possible_entry = []
			self.all_possible_exit_states = []
			global_entry_requirements = d['global_state_entry_requirements']
			for e in global_entry_requirements:
				self.all_possible_entry.append(e)
				subnode_state_updates = d['subnode_state_updates']
				for subnode in subnode_state_updates:
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
						exit_state[key] = d['global_post_supernode_state_updates'][key]
					self.all_possible_exit_states.append(exit_state)

	def does_edge_exist(self, second_node):
		# treat self as src, second_node as dst
		exit_conds = self.all_possible_exit_states
		entry_conds = second_node.all_possible_entry
		for i in entry_conds:
			for e in exit_conds:
				equal = True
				for key in i:
					# if 'bot_asked_singer' in e:
					# 	print('laj', i, e, key)
					if key not in e:
						if type(i[key]) == type(True) and i[key] == True:
							equal = False
						elif type(i[key]) != type(True) and i[key] != 'None': 
							equal = False
					elif i[key] != e[key]:
						# print('wtf', i, e, key)
						equal = False
				if equal:
					return True

		return False

# MAKE ALL OF FOLLOWING WORK WITH COMMAND LINE ARGS (to any specific yaml dir)

'''
./music_get_song/supernode.yaml
./music_get_instrument/supernode.yaml
./music_get_singer/supernode.yaml
./music_handle_opinion/supernode.yaml
./music_ask_song/supernode.yaml
./music_ask_singer_respond_til/supernode.yaml
./music_ask_singer/supernode.yaml
./instrument_til_reply/supernode.yaml
./exit/supernode.yaml
./music_response_to_song/supernode.yaml
./music_introductory/supernode.yaml
./music_handoff/supernode.yaml
'''

intro = TreeletNode('supernodes/music_introductory/supernode.yaml')
handle_op = TreeletNode('supernodes/music_handle_opinion/supernode.yaml')
ask_song = TreeletNode('supernodes/music_ask_song/supernode.yaml')
ask_sing = TreeletNode('supernodes/music_ask_singer/supernode.yaml')
ask_sing_til = TreeletNode('supernodes/music_ask_singer_respond_til/supernode.yaml')
get_instr = TreeletNode('supernodes/music_get_instrument/supernode.yaml')
instr_til = TreeletNode('supernodes/instrument_til_reply/supernode.yaml')
get_sing = TreeletNode('supernodes/music_get_singer/supernode.yaml')
get_song = TreeletNode('supernodes/music_get_song/supernode.yaml')
respond_song = TreeletNode('supernodes/music_response_to_song/supernode.yaml')
handoff = TreeletNode('supernodes/music_handoff/supernode.yaml')
exit = TreeletNode('supernodes/exit/supernode.yaml')

# print('chungoose', get_instr.does_edge_exist(get_instr))

G = {}

nodes = [intro, handle_op, get_instr, instr_til, get_sing, get_song, respond_song, ask_song, ask_sing, ask_sing_til, handoff, exit]
for i in range(len(nodes)):
	for j in range(i, len(nodes)):
		src = nodes[i]
		dst = nodes[j]
		if src.does_edge_exist(dst):
			if src.name + ' ' not in G:
				G[src.name + ' '] = [dst.name + ' ']
			else:
				G[src.name + ' '].append(dst.name + ' ')

del G[exit.name + ' ']

is_cylic = cyclic(G)
if is_cylic:
	print('Treelet Graph is cyclic. Fix yaml files')
	sys.exit(1)

print('treelet graph', G)
print('--------')
self_loops = set()
no_cycle_G = {}
for key in G:
	no_cycle_G[key] = []
	for child in G[key]:
		if child != key:
			no_cycle_G[key].append(child)
		else:
			self_loops.add(child[:-1])

# G = {'0 ': ['1 '], '1 ': ['2 ', '3 ', '4 '], '2 ': ['3 ', '4 '], '3 ': ['4 ', '5 '], '4 ': ['6 ', '8 '], '5 ': ['7 '], '6 ': ['7 '], '7 ': ['8 ']}
# print('chungus')
paths = find_all_paths(find_all_parents(no_cycle_G, 'music_introductory '), 'music_introductory ', 'exit ')

# print(paths[0].split())
# self_loops = {'2', '4', '6'}

print('number of unique convo paths between music_introductory and exit: {}'.format(len(paths)))
print('---- List of unique paths --------')
for p in paths:
	print(p)
print('-----------')

# print('number of convo paths including self loops: {}'.format(count_with_self_loops(paths, self_loops)))

draw_graph = True
if draw_graph:
	nx_G = nx.DiGraph()
	for key in G:
		for child in G[key]:
			nx_G.add_edge(key[:-1], child[:-1])
	nx.draw(nx_G, with_labels = True, node_size=800)
	plt.show()

### other stuff


# Verify every state access exists in initial state
state_vals = set()
for n in nodes:
	for d in n.all_possible_entry:
		for key in d:
			state_vals.add(key)
	for d in n.all_possible_exit_states:
		for key in d:
			state_vals.add(key)
state_vals = list(state_vals)
state_vals.sort()
for t in state_vals:
	print(t)
# Very every func call in NLG exists in nlg_helpers
# verify that a node contains and intro & exit node
# Verify that variables that need to be exposed are actually exposed in nlg.yaml
# Verify that all subnodes defined in supernode.yaml exist in nlg.yaml
# Robust error logging when something in yaml causes crash
# Verify all yamls obey correct format (correct categories, etc.)
