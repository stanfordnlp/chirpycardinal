import os
import yaml

ALL_FLAGS_PATH = os.path.join(os.path.dirname(__file__), '../../symbolic_rgs/flags.yaml')
with open(ALL_FLAGS_PATH, 'r') as f:
	ALL_FLAGS = yaml.safe_load(f)
	
def nlu_processing(func):
	def f(*args, **kwargs):
		nlu_flags = {}
		def add_nlu_flag(flag_name, val=True):
			assert flag_name in ALL_FLAGS, f"Flag name {flag_name} not found in flags.yaml!"
			nlu_flags[flag_name] = val
		def add_nlu_flags(flag_name_to_val):
			for flag_name in flag_name_to_val.keys():
				assert flag_name in ALL_FLAGS, f"Flag name {flag_name} not found in flags.yaml!"
			nlu_flags.update(flag_name_to_val)
		func.__globals__['ADD_NLU_FLAG'] = add_nlu_flag
		func.__globals__['ADD_NLU_FLAGS'] = add_nlu_flags
		func(*args, **kwargs)
		return nlu_flags
	return f
		
def get_default_flags():
	return {flag: False for flag in ALL_FLAGS}