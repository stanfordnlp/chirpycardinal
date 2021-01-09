import os
import csv
import argparse
import random
from collections import Counter

def read_csv(path):
    with open(path, 'r') as f:
        reader = csv.reader(f)
        next(reader) # get rid of header
        return list(reader)

def write_to_csv(path, responses):
    with open(path, 'a') as f:
        writer = csv.writer(f)
        writer.writerows(responses)

TYPE_OF_OFFENSES = {1: 'sexual', 2:'criticism', 3:'curse', 4:'inappropriate topic', 5:'bodily harm', 6:'error'}

def label1():
    offensive_responses = read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'offensive_responses.csv'))
    labeled_type = read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'type_of_offenses.csv'))
    labeled_type_set = set([utterance for _, rg, utterance, _, annotator in labeled_type if annotator == ANNOTATOR])
    offensive_responses_counter = Counter([response for _, _, response in offensive_responses])
    sorted_offensive_responses = [response for response, _ in offensive_responses_counter.most_common()]
    responses = []
    for offensive_user_response in sorted_offensive_responses:
        contexts_for_offense = set([(bot_utterance, response_rg, response) for bot_utterance, response_rg, response in offensive_responses if response == offensive_user_response])
        context_rg = random.choice([rg for _, rg, _ in contexts_for_offense])
        if offensive_user_response in labeled_type_set:
            continue
        offense = random.choice([offense for offense in contexts_for_offense if offense[1] == context_rg])
        response = ''
        while not response.isdigit():
            print(f'>> [{context_rg}] {offense[0]} \033[91m{offense[-1]}\033[00m')
            type_offense_str = ' '.join([f'[{i}] {t};' for i, t in TYPE_OF_OFFENSES.items()])
            print(f'Is this {type_offense_str} type "exit" to exit')
            response = input('? ')
            if response == 'exit':
                return responses
        responses.append(offense + (response, ANNOTATOR))
    print(">>> ALL DONE")
    return responses

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('annotator', type=str, help='The name of the annotator')
    ANNOTATOR = parser.parse_args().annotator
    responses = label1()
    write_to_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'type_of_offenses.csv'), responses)
