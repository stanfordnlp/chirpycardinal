"""
Backtests a conversation against blenderbot.
"""

import argparse
import os
import requests

def dir_path(string):
	if os.path.exists(string):
		return string
	else:
		raise NotADirectoryError(string)


parser = argparse.ArgumentParser()
parser.add_argument('path', type=dir_path)
parser.add_argument('--prefix', default="", type=str)

arguments = parser.parse_args()
with open(arguments.path, 'r') as f:
	lines = [x.strip() for x in f.readlines()]

lines = [x for x in lines if x]
print('\n'.join(lines))
json = {
	"history": lines,
	"prefix": arguments.prefix,
}
result = requests.post("http://localhost:4087", json=json)
result = result.json()
for response, score in zip(result['responses'], result['response_probabilities']):	
	print(f"[{score:.3f}]\t{response}")
#print(result.json())