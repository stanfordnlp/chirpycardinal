import json
import requests

with open('sentences.txt', 'r') as sentences_file:
    sentences = [line.strip() for line in sentences_file]
    sentences = [sentence for sentence in sentences if ']]' not in sentence]

with open('response_templates.json', 'r') as response_templates_file:
    response_templates = json.load(response_templates_file)

temperature = 0.6
top_p = 0.1

out = requests.post('http://localhost:5001', json={
    'sentences': sentences,
    'tuples': response_templates['location'],
    'num_beams': 2,
    'num_return_sequences': 1,
    'do_sample': False,
    'min_length': 2,
    'length_penalty': 5,
    # 'num_beam_groups': 5,
    # 'diversity_penalty': 5000,
    'max_length': 50
})
"""
out = requests.post('http://localhost:5001', json={
    'sentences': sentences,
    'tuples': response_templates['location'],
    'temperature': 0.8,
    'top_p': 0.9,
    'top_k': 20,
    'num_beams': 1,
    'num_return_sequences': 10,
    'do_sample': True,
    'min_length': 2,
    'max_length': 30
})"""


print(out)

data = out.json()

print(f"Finished in: {data['performance'][0]:.3f} sec.")

for completion, context, prompt in zip(data['completions'], data['contexts'], data['prompts']):
    print('Prompt:    ', prompt)
    print('Completion:', completion)
    print('Context:   ', context)
    print()
# print(out.json())

