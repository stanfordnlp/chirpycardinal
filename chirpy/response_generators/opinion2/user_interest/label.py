from collections import defaultdict
import os
import csv
import argparse

def read_csv(path):
    with open(path, 'r') as f:
        reader = csv.reader(f)
        return list(reader)

def write_to_csv(path, responses):
    with open(path, 'a') as f:
        writer = csv.writer(f)
        writer.writerows(responses)

parser = argparse.ArgumentParser()
parser.add_argument('annotator', type=str, help='The name of the annotator')
ANNOTATOR = parser.parse_args().annotator
PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'common_solicit_reason_responses.csv')
WRITE_TO_PATH = PATH.replace('.csv', '_labeled.csv')
potential_labels = {1: 'continue', 2: 'exit'}

def label1(path):
    utterances = [utterance for utterance, count in read_csv(path)]
    responses = []
    for utterance in utterances:
        response = ''
        while not response.isdigit():
            print(f'>> \033[92m{utterance}\033[00m {potential_labels}')
            response = input('? ')
            if response == 'exit': 
                return responses
        responses.append((utterance, potential_labels[int(response)], ANNOTATOR))
    return responses

def inter_annotator_agreement(path):
    rows = read_csv(path)
    grouped_by_annotator = defaultdict(dict)
    for utterance, label, annotator in rows:
        grouped_by_annotator[annotator][utterance] = label
    utterances = set(row[0] for row in rows)
    agree_lst = []
    disagree_lst = []
    for utterance in utterances:
        labels = set([labeled[utterance] for labeled in grouped_by_annotator.values()])
        if len(set(labels)) == 1:
            agree_lst += [utterance]
        else:
            disagree_lst += [(utterance, labels)]
    return agree_lst, disagree_lst, len(agree_lst) / (len(agree_lst) + len(disagree_lst))

if __name__ == "__main__":
    responses = label1(PATH)
    write_to_csv(WRITE_TO_PATH, responses)
    agrees, disagrees, ratio = inter_annotator_agreement(WRITE_TO_PATH)
    print(ratio)
    print(disagrees)